import typing
from collections.abc import Iterable
import abc
import logging
import json
from shutil import which
from subprocess import check_output
from argparse import ArgumentParser, Namespace

from .util import CommandProvider
from .config import ChrispileConfig

logger = logging.getLogger(__name__)


class GuessingException(Exception):
    """
    For when we can't detect something about the system we need to know.
    """
    pass


class Endpoint(abc.ABC):
    """
    An Endpoint represents something about the system. It has a name,
    and can be represented as either a string value or some shell code.
    """
    OPTION_NAME = 'option'

    def __init__(self, config: ChrispileConfig):
        self.value: str = config.__dict__[self.OPTION_NAME]
        self.config = config
        if not self.value:
            self.value = self.guess(config)

    @classmethod
    def guess(cls, config: ChrispileConfig) -> typing.Optional[str]:
        """
        Figure out the value automatically.
        :raises GuessingException: can't detect from system
        :return: value
        """
        return None

    def _as_shell(self, value: str, options: typing.Iterable) -> str:
        return value

    def as_shell(self, options: typing.Optional[Iterable] = None) -> str:
        """
        Produce a representation of this value which can be passed to docker/podman
        :return: option for docker/podman
        """
        if options is None:
            options = []
        return self._as_shell(self.value, options)

    def __str__(self):
        return str(self.value)


class EngineEndpoint(Endpoint):
    OPTION_NAME = 'engine'
    SUPPORTED_ENGINES = ['podman', 'docker']

    @classmethod
    def guess(cls, config):
        for engine_name in cls.SUPPORTED_ENGINES:
            if which(engine_name):
                return engine_name
        raise GuessingException(
            'No supported engines detected. '
            'Options are: ' + str(cls.SUPPORTED_ENGINES)
        )


class SelinuxEndpoint(Endpoint):
    OPTION_NAME = 'selinux'

    @classmethod
    def guess(cls, config):
        if not which('getenforce'):
            return 'na'
        return check_output(['getenforce'], encoding='utf-8').strip().lower()

    def _as_shell(self, value, options):
        if value != 'enforcing':
            return ''
        if not options:
            return '1'
        if options[0] == 'mount_flag':
            return ',z'
        raise ValueError('unrecognized options: ' + str(options))


class GpuEndpoint(EngineEndpoint):
    OPTION_NAME = 'gpu'

    def __init__(self, config: ChrispileConfig):
        super().__init__(config)

    @classmethod
    def guess(cls, config):
        if which('nvidia-container-toolkit'):
            return 'nvidia-container-toolkit'
        return None

    def _as_shell(self, value, options):
        if not value:
            return ''

        flags = []
        engine = str(EngineEndpoint(self.config))
        selinux = SelinuxEndpoint(self.config).as_shell()
        if selinux == '1':
            flags.append('--security-opt')
            flags.append('label=type:nvidia_container_t')

        if engine == 'docker':
            output = check_output([engine, 'info', '--format', '{{ (json .Runtimes) }}'], text=True)
            runtimes = json.loads(output)
            if 'nvidia' in runtimes:
                flags.append('--runtime=nvidia')
            else:
                output = check_output([engine, 'run', '--help'], text=True)
                if '--gpus' in output:
                    flags.append('--gpus')
                    which_gpus = options[0] if options else 'all'
                    flags.append(which_gpus)
                else:
                    logger.warning(f'Unsure how to use GPU with {engine}')
        return ' '.join(flags)


class AbstractChrispileApi(abc.ABC):
    ENDPOINT_CLASSES = [EngineEndpoint, GpuEndpoint, SelinuxEndpoint]

    def __init__(self, config: ChrispileConfig = None):
        if not config:
            config = ChrispileConfig()

        self.config = config

    @classmethod
    @abc.abstractmethod
    def endpoint2value(cls, endpoint: Endpoint, args: Iterable) -> str:
        ...

    def engine(self, *args):
        return self.endpoint2value(EngineEndpoint(self.config), args)

    def gpu(self, *args):
        return self.endpoint2value(GpuEndpoint(self.config), args)

    def selinux(self, *args):
        return self.endpoint2value(SelinuxEndpoint(self.config), args)

    @classmethod
    def get_class_names(cls):
        return [ec.OPTION_NAME for ec in cls.ENDPOINT_CLASSES]


class ShellBuilderApi(AbstractChrispileApi):
    @staticmethod
    def endpoint2value(endpoint: Endpoint, args: Iterable) -> str:
        return endpoint.as_shell(args)


class InfoApi(AbstractChrispileApi):
    @staticmethod
    def endpoint2value(endpoint: Endpoint, args: Iterable) -> str:
        return str(endpoint)


class ChrispileApiCommand(CommandProvider):
    # assign strings to methods of an AbstractChrispileApi
    ENDPOINT_MAP = {
        'engine': lambda e: e.engine,
        'gpu': lambda e: e.gpu,
        'selinux': lambda e: e.selinux
    }

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)
        self.engine = str(EngineEndpoint(self.config))

        output_format = parser.add_mutually_exclusive_group()
        output_format.add_argument('-f', '--as-flag',
                                   dest='as_flag',
                                   action='store_true',
                                   help=f'format output as shell flag for {self.engine}')
        output_format.add_argument('-s', '--as-string',
                                   dest='as_string',
                                   action='store_true',
                                   help=f'format output as plain string (default)')
        endpoint_options = str(list(self.ENDPOINT_MAP.keys()))
        parser.add_argument('endpoint',
                            type=self.endpoint_name,
                            help='key for information which to retrieve'
                                 ' ' + endpoint_options)
        parser.add_argument('subkeys',
                            nargs='*',
                            help='name of which field of information to '
                                 'retrieve under given endpoint')

    @classmethod
    def endpoint_name(cls, endpoint_name):
        endpoint_name = str(endpoint_name)
        if endpoint_name not in cls.ENDPOINT_MAP:
            raise ValueError(f'{endpoint_name} is not one of: {str(cls.ENDPOINT_MAP.keys())}')
        return endpoint_name

    def __call__(self, options: Namespace):
        api_class = ShellBuilderApi if options.as_flag else InfoApi
        api_instance = api_class(self.config)
        api_function = self.ENDPOINT_MAP[options.endpoint](api_instance)
        result = api_function(*options.subkeys)
        print(result)
