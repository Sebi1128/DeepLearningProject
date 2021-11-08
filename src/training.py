from tqdm import tqdm
import wandb
import torch

def epoch_run(model, active_dataset, optimizer, run_no, model_writer, cfg):
    pbar = tqdm(range(cfg.n_epochs))
    for epoch_no in pbar:
        c_train_loss, r_train_loss = train_epoch(model, active_dataset, optimizer, 
                                                 batch_size=cfg.batch_size, device=cfg.device)
        c_valid_loss, r_valid_loss = validate_epoch(model, active_dataset, 
                                                    batch_size=cfg.batch_size, device=cfg.device)

        info_text = f"{run_no+1}|C|R Train: {c_train_loss:.5f}|{r_train_loss:.5f}"
        info_text += f"  Valid: {c_valid_loss:.5f}|{r_valid_loss:.5f}"
        pbar.set_description(info_text, refresh=True)

        wandb.log({"r_train_loss": r_train_loss, "c_train_loss": c_train_loss})
        wandb.log({"r_valid_loss": r_valid_loss, "c_valid_loss": c_valid_loss})

        if not (epoch_no and run_no): # initialization
            r_best_valid_loss = r_valid_loss
            c_best_valid_loss = c_valid_loss
            model_writer.write(model, 'c_')
            model_writer.write(model, 'r_')
        else:
            if r_valid_loss < r_best_valid_loss:
                r_best_epoch_no = epoch_no
            if c_valid_loss < c_best_valid_loss:
                c_best_epoch_no = epoch_no

        if not epoch_no:
            r_best_epoch_no = -1
            c_best_epoch_no = -1

    print(f"Best Classification Loss \t{c_best_valid_loss} with Epoch No {c_best_epoch_no} for Run {run_no}")
    print(f"Final Reconstruction Loss \t{r_best_valid_loss} with Epoch No {r_best_epoch_no} for Run {run_no}")


def train_epoch(model, active_data, optimizer, batch_size, device):

    model.train()
    torch.set_grad_enabled(True)
    
    iter_schedule = active_data.get_itersch(uniform=False)

    lbld_DL = active_data.get_loader('labeled', batch_size=batch_size)
    # realize that we can use whole dataset as unlabeled
    unlbld_DL = active_data.get_loader('train', batch_size=batch_size) 

    lbl_iter = iter(lbld_DL)
    unlbl_iter = iter(unlbld_DL)

    n_epochs = len(active_data.trainset) // batch_size

    c_losses = list()
    r_losses = list()
    
    for is_labeled in iter_schedule[:n_epochs]:

        if is_labeled:
            x, t = next(lbl_iter)
            x = x.to(device)
            t = t.to(device)
            c = model.classify(x)
            loss = model.c_loss(c, t)
            c_losses.append(loss)
        else:
            x, _ = next(unlbl_iter)
            x = x.to(device)
            r = model.reconstruct(x)
            loss = model.r_loss(r.flatten(), x.flatten())
            r_losses.append(loss)
            
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    mean_c_loss = torch.mean(torch.tensor(c_losses))
    mean_r_loss = torch.mean(torch.tensor(r_losses))

    return mean_c_loss, mean_r_loss

        
def validate_epoch(model, active_data, batch_size, device):

    model.eval()
    torch.set_grad_enabled(False)

    valid_DL = active_data.get_loader('validation', batch_size=batch_size)

    c_losses = list()
    r_losses = list()
    
    for x, t in valid_DL:
            
        x = x.to(device)
        t = t.to(device)
        c = model.classify(x)
        loss = model.c_loss(c, t)
        c_losses.append(loss)

    for x, t in valid_DL:

        x = x.to(device)
        t = t.to(device)

        r = model.reconstruct(x)
        loss = model.r_loss(r.flatten(), x.flatten())
        r_losses.append(loss)
        
    mean_c_loss = torch.mean(torch.tensor(c_losses))
    mean_r_loss = torch.mean(torch.tensor(r_losses))

    return mean_c_loss, mean_r_loss