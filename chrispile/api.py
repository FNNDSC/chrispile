import typing
import abc
import logging
import json
from shutil import which
from subprocess import check_output
from argparse import ArgumentParser, Namespace

from .util import CommandProvider
from .config import ChrispileConfig, get_config

logger = logging.getLogger(__name__)


class GuessingException(Exception):
    """
    For when we can't detect something about the system we need to know.
    """
    pass


class Endpoint(abc.ABC):
    OPTION_NAME = 'option'

    def __init__(self, config: ChrispileConfig):
        self.value: str = config.__dict__[self.OPTION_NAME]
        self.config = config
        if not self.value:
            self.value = self.guess(config)

    @staticmethod
    def guess(self, config: ChrispileConfig) -> typing.Optional[str]:
        """
        Figure out the value automatically.
        :raises GuessingException: can't detect from system
        :return: value
        """
        return None

    def _as_shell(self, value: str, options: list) -> str:
        return value

    def as_shell(self, options: typing.Optional[list] = None) -> str:
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

    def guess(self, config):
        for engine_name in self.SUPPORTED_ENGINES:
            if which(engine_name):
                return engine_name
        raise GuessingException(
            'No supported engines detected. '
            'Options are: ' + str(self.SUPPORTED_ENGINES)
        )


class SelinuxEndpoint(Endpoint):
    OPTION_NAME = 'selinux'

    def guess(self, config):
        if not which('getenforce'):
            return 'na'
        return check_output(['getenforce'], encoding='utf-8').strip().lower()

    def _as_shell(self, value, options):
        if value != 'enforcing':
            return ''
        if not options:
            return 1
        if options[0] == 'mount_flag':
            return ',z'
        raise ValueError('unrecognized options: ' + str(options))


class GpuEndpoint(Endpoint):
    OPTION_NAME = 'nvidia'
    SHELL_MAP = {
        'nvidia-container-runtime': '--runtime=nvidia',
        'native': '--gpus all'
    }

    def __init__(self, config: ChrispileConfig):
        super().__init__(config)
        self.selinux = SelinuxEndpoint(config).as_shell()

    def guess(self, config):
        engine = str(EngineEndpoint(config))
        if engine == 'podman':
            logger.warning('GPU detection for podman not implemented')
            return None
        if engine == 'docker':
            output = check_output([engine, 'info', '--format', '{{ (json .Runtimes) }}'], encoding='utf-8')
            runtimes = json.loads(output)
            if 'nvidia' in runtimes:
                return 'nvidia-container-runtime'
            elif which('nvidia-container-runtime-hook'):
                return 'native'
            else:
                return None

    def _as_shell(self, value, options):
        if not value:
            return ''
        result = self.SHELL_MAP[value]
        if self.selinux == '1':
            result += '--security-opt label=type:nvidia_container_t'
        return result


class ChrispileApi(CommandProvider):

    ENDPOINT_MAP = {
        'engine': EngineEndpoint,
        'gpu': GpuEndpoint,
        'selinux': SelinuxEndpoint
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
                            nargs='+',
                            help='key for information which to retrieve ' + endpoint_options)

    def __call__(self, options: Namespace):
        endpoint = options.endpoint[0]
        if endpoint not in self.ENDPOINT_MAP:
            raise ValueError(f'{endpoint} is not one of: {str(self.ENDPOINT_MAP.keys())}')

        endpoint_class = self.ENDPOINT_MAP[endpoint]
        endpoint_instance = endpoint_class(self.config)

        if options.as_flag:
            result = endpoint_instance.as_shell(options.endpoint[1:])
        else:
            result = str(endpoint_instance)
        print(result)
