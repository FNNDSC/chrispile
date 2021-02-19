from __future__ import annotations

from typing import Optional
from os import path, environ, getenv
from yaml import safe_load

CHRISPILE_UUID = '51c01992-5987-4fa0-bd76-571681f5c9fa'

CONFIG_FILE = path.join(environ['HOME'], '.config', 'fnndsc', 'chrispile.yml')
CONFIG_FILE = getenv('CHRISPILE_CONFIG_FILE', CONFIG_FILE)

DEFAULT_CONFIG = {
    'bin_folder': '~/.local/bin',
    'engine': None,  # podman, docker
    'gpu': None,  # nvidia-container-toolkit
    'selinux': None  # enforcing, permissive, disabled
}


class ChrispileConfig:
    def __init__(self,
                 bin_folder: Optional[str] = None,
                 engine: Optional[str] = None,
                 gpu: Optional[str] = None,
                 selinux: Optional[str] = None,
                 default: Optional[ChrispileConfig] = None):

        self.bin_folder = bin_folder
        self.engine = engine
        self.gpu = gpu
        self.selinux = selinux

        default = default.__dict__ if default else DEFAULT_CONFIG

        for field in self.__dict__:
            if self.__dict__[field] is None and field in default:
                self.__dict__[field] = default[field]


def get_config() -> ChrispileConfig:
    custom_config = {}
    if path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            custom_config = safe_load(''.join(f.readlines()))
    return ChrispileConfig(**custom_config)
