from os import path, environ, getenv
from yaml import safe_load

CHRISPILE_UUID = '51c01992-5987-4fa0-bd76-571681f5c9fa'

CONFIG_FILE = path.join(environ['HOME'], '.config', 'fnndsc', 'chrispile.yml')
CONFIG_FILE = getenv('CHRISPILE_CONFIG_FILE', CONFIG_FILE)

DEFAULT_CONFIG = {
    'bin_folder': '~/.local/bin',
    'engine': None,  # podman, docker
    'nvidia': None,  # nvidia-container-toolkit, legacy
    'selinux': None  # enforcing, permissive, disabled
}


class ChrispileConfig:
    def __init__(self, custom_config: dict = None, default_config: dict = None):
        if custom_config is None:
            custom_config = {}
        if default_config is None:
            default_config = DEFAULT_CONFIG

        merged_config = dict()
        merged_config.update(default_config)
        merged_config.update(custom_config)

        self.engine = merged_config['engine']
        self.nvidia = merged_config['nvidia']
        self.selinux = merged_config['selinux']
        self.bin_folder = merged_config['bin_folder']


def get_config() -> ChrispileConfig:
    custom_config = {}
    if path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            custom_config = safe_load(''.join(f.readlines()))
    return ChrispileConfig(custom_config)
