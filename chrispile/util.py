import abc
from argparse import ArgumentParser, Namespace
from .config import get_config


class CommandProvider(abc.ABC):
    def __init__(self, parser: ArgumentParser):
        self.config = get_config()
        parser.set_defaults(func=self)

    @abc.abstractmethod
    def __call__(self, options: Namespace):
        raise NotImplementedError()
