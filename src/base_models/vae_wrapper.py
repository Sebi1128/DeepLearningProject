# https://pytorch-lightning-bolts.readthedocs.io/en/latest/autoencoders.html
from torch import nn
from pl_bolts.models.autoencoders import VAE


class VAEWrapper(nn.Module):
    def __init__(self, cfg):
        super(VAEWrapper, self).__init__()
        self.cfg = cfg

        self.vae = VAE(input_height=32)
        self.vae = self.vae.from_pretrained('cifar10-resnet18')
        self.vae.freeze()

    def get_encoder(self):
        return EncoderWrapper(self.cfg.enc, self.vae.encoder)

    def get_decoder(self):
        return DecoderWrapper(self.cfg.dec, self.vae.decoder)

    def get_bottleneck(self):
        return BottleneckWrapper(self.cfg.btk, self.vae.fc_mu, self.vae.fc_var, self.vae.sample)


class EncoderWrapper(nn.Module):
    def __init__(self, cfg_enc, encoder):
        super(EncoderWrapper, self).__init__()
        self.cfg_enc = cfg_enc
        self.encoder = encoder

    def forward(self, x):
        return self.encoder(x)


class DecoderWrapper(nn.Module):
    def __init__(self, cfg_dec, decoder):
        super(DecoderWrapper, self).__init__()
        self.cfg_dec = cfg_dec
        self.decoder = decoder
        self.loss = None

    def forward(self, z):
        return self.decoder(z)


class BottleneckWrapper(nn.Module):
    def __init__(self, cfg_bot, fc_mu, fc_var, sample):
        super(BottleneckWrapper, self).__init__()
        self.cfg_bot = cfg_bot
        self.fc_mu = fc_mu
        self.fc_var = fc_var
        self.sample = sample

    def forward(self, x):
        mu = self.fc_mu(x)
        log_var = self.fc_var(x)
        p, q, z = self.sample(mu, log_var)
        latent = [z, mu, log_var]
        return z, latent
