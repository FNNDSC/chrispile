import sys
import json
from os import path
from subprocess import check_output, run, CalledProcessError
from pkg_resources import parse_version
from importlib.metadata import Distribution
from jinja2 import Environment, PackageLoader
from .api import ShellBuilderApi, AbstractChrispileApi, Endpoint
from .config import ChrispileConfig, CHRISPILE_UUID


class PluginMetaLookupError(Exception):
    pass


class PythonImageInfo:
    """
    Use the docker command line to get information about an image,
    which is assumed to be Python-based.
    """
    def __init__(self, engine):
        self.engine = engine

    def get_plugin_cmd(self, dock_image: str) -> str:
        try:
            selfexec = check_output(
                [self.engine, 'inspect', '--format', '{{ (index .Config.Cmd 0) }}', dock_image],
                text=True
            )
        except CalledProcessError:
            raise PluginMetaLookupError(f"could not run '{self.engine} inspect {dock_image}'")
        return selfexec.strip()

    def get_plugin_meta(self, dock_image: str) -> dict:
        cmd = [self.engine, 'run', '--rm', dock_image, self.get_plugin_cmd(dock_image), '--json']
        try:
            meta = check_output(cmd, text=True)
        except CalledProcessError:
            raise PluginMetaLookupError(f"could not run '{' '.join(cmd)}'")
        try:
            return json.loads(meta)
        except json.JSONDecoder:
            raise PluginMetaLookupError(f"Command '{' '.join(cmd)}' produced invalid JSON")

    def interrogate_python_package_location(self, dock_image: str, meta: dict) -> str:
        python_version_string = check_output(
            [
                self.engine, 'run', '--rm', '-w', '/',
                '--entrypoint', 'python',
                dock_image,
                '--version'
            ],
            text=True
        )
        python_version_number = python_version_string.split()[-1]
        if parse_version(python_version_number) >= parse_version('3.7'):
            # this part is inconsistent across versions
            # New behavior in python3.9: importlib.resources.path(package, '') raises IsADirectoryError
            detected_path = check_output(
                [
                    self.engine, 'run', '--rm', '-w', '/',
                    '--entrypoint', 'python',
                    dock_image,
                    '-c',
                    'from importlib.resources import path\n'
                    'from os.path import dirname\n'
                    f'with path("{meta["selfexec"]}", "__init__.py") as p: print(dirname(p))'
                ],
                encoding='utf-8'
            )
            detected_path = detected_path.strip()
        else:
            short_version_number = python_version_number[:3]
            detected_path = f'/usr/local/lib/python{short_version_number}' \
                            f'/site-packages/{meta["selfexec"]}'
        run(
            [
                self.engine, 'run', '--rm', '-w', '/',
                '--entrypoint', 'sh',
                dock_image,
                '-c', 'test -f ' + path.join(detected_path, "__init__.py")
            ],
            check=True
        )
        return detected_path

    def find_resource_dir(self, dock_image: str, meta: dict) -> str:
        """
        Attempt to find the resource directory for the python package of the ChRIS plugin.

        It usually looks like /usr/local/lib/python3.9/site-packages/something

        If unsuccessful, return empty string.
        :param dock_image: container image tag
        :param meta: plugin meta
        :return: package location inside image
        """
        try:
            return self.interrogate_python_package_location(dock_image, meta)
        except CalledProcessError:
            return ''


class SubShellApi(AbstractChrispileApi):
    """
    Produces shell subshell syntax for how to query chrispile api.
    """
    @classmethod
    def endpoint2value(cls, endpoint: Endpoint, args: list) -> str:
        extra_options = ''
        if args:
            extra_options = ' ' + ' '.join(args)
        # btw hard-coded program and subcommand name
        return f'$(chrispile api --as-flag {endpoint.OPTION_NAME}{extra_options})'


# noinspection SpellCheckingInspection
class Chrispiler:
    def __init__(self, config: ChrispileConfig):
        pkg = Distribution.from_name(__package__)
        eps = [ep for ep in pkg.entry_points if ep.group == 'console_scripts']
        self.program_name = eps[0].name

        jinja_env = Environment(loader=PackageLoader(__package__, 'templates'))
        self.template = jinja_env.get_template('exec.sh')
        self.config = config

    def compile_plugin(self, dock_image: str, linking='dynamic') -> str:
        """
        Generate a shell script for running a dockerized ChRIS plugin.

        There are two "linking" strategies:

        - static: the options for ``docker run ...`` are resolved by
          this function.
        - dynamic: the shell script will make calls to ``chrispile api ...``
          and build a ``docker run ...`` command on-the-fly.
          Moreover, advanced features become available and are supported by
          ``chrispile run`` liike doing a dry run (to print the ``docker run``
          command) or mounting the Python source folder into the container
          for development.
        :param dock_image: container image tag of ChRIS plugin
        :param linking: linking strategy
        :raises PluginMetaLookupError: docker image probably not pulled
        :return: code for a shell script
        """
        if linking not in ['static', 'dynamic']:
            raise ValueError('linking must be either "static" or "dynamic"')

        api = ShellBuilderApi(self.config)
        engine = api.engine()
        info = PythonImageInfo(engine)
        # TODO might be useful to get plugin meta dynamically
        meta = info.get_plugin_meta(dock_image)

        return self.template.render(
            linking=linking,
            info=info,
            ShellBuilderApi=api,
            SubShellApi=SubShellApi(self.config),
            meta=meta,
            dock_image=dock_image,
            selfexec=meta['selfexec'],
            chrispile=self.program_name,
            chrispile_uuid=CHRISPILE_UUID,
        )

    def test_the_waters(self, dock_image: str):
        """
        Same as get_plugin_cmd but if unsuccessful, print some advice and exit.
        :param dock_image: container image tag of a ChRIS plugin
        :return: command inside image to run
        """
        engine = ShellBuilderApi(self.config).engine()

        try:
            return PythonImageInfo(engine).get_plugin_cmd(dock_image)
        except PluginMetaLookupError as e:
            print('Failed to get plugin meta', end=': ')
            print(e)
            print(f'\nTry running `{engine} pull {dock_image}`')
            sys.exit(1)
