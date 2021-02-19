import sys
import stat
import os
import pwd
from os import path
from argparse import Namespace, ArgumentParser
import logging

from .render import Chrispiler
from .util import CommandProvider
from .config import CHRISPILE_UUID

logger = logging.getLogger(__name__)


class ChrispileInstaller(CommandProvider):
    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)
        parser.add_argument('-o', '--output',
                            help="output to file. "
                                 "Special value '-' means print to stdout."
                                 "If not specified, the script is installed "
                                 f"to {self.config.bin_folder}")
        parser.add_argument('-U', '--upgrade',
                            action='store_true',
                            help='Overwrite target if already exists')

        linking = parser.add_mutually_exclusive_group()
        linking.add_argument('-s', '--static',
                             action='store_true',
                             help="resolve the script's dependency on %(prog)s itself")
        linking.add_argument('-d', '--dynamic',
                             action='store_true',
                             help='produce a script which resolves system information '
                                  'at runtime via %(prog) api')
        parser.add_argument('dock_image',
                            help='container image of the ChRIS plugin')

    def __call__(self, options: Namespace):
        compiler = Chrispiler(self.config)
        name = compiler.test_the_waters(options.dock_image)

        linking = 'static' if options.static else 'dynamic'

        # compiling of a ChRIS plugin involves starting and stopping a
        # docker container which takes an annoying second of time which
        # is why we have this line of code duplicated.
        lazy_compile = lambda: compiler.compile_plugin(options.dock_image, linking)

        if options.output == '-':
            code = lazy_compile()
            print(code)
            return

        if options.output:
            target = options.output
            output_name = target
        else:
            bin_folder = self.get_installation_dir()
            target = path.join(bin_folder, name)
            output_name = name

        if path.exists(target) and not options.upgrade:
            logger.error('%s exists. Pass -U to overwrite', target)
            sys.exit(1)

        code = lazy_compile()
        with open(target, 'w', encoding='utf-8') as f:
            f.write(code)

        os.chmod(target, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        print(output_name)

    def get_installation_dir(self) -> str:
        """
        Get from config the bin folder where to install.
        Show a warning and how to fix if folder is not in $PATH
        :return: bin folder
        """
        bin_folder = path.expanduser(self.config.bin_folder)
        os.makedirs(bin_folder, exist_ok=True)

        path_list = os.environ['PATH'].split(':')
        if bin_folder not in path_list:
            logger.warning('%s not in $PATH', bin_folder)

            shell = path.basename(pwd.getpwuid(os.geteuid()).pw_shell)
            if shell in ['bash', 'zsh']:
                logger.warning('To fix, run this command yourself: ')
                logger.warning("\n\techo 'export PATH=%s:$PATH' >> ~/.%src\n", bin_folder, shell)

        return bin_folder


def is_product(filename: str) -> bool:
    """
    Detect whether given file was created by chrispile by
    looking for the UUID in its last line.
    :param filename: file name
    :return: true if file was created by chrispile
    """
    search_string = f'# CHRISPILE {CHRISPILE_UUID}'
    with open(filename, 'rb') as f:
        f.seek(-len(search_string), os.SEEK_END)
        last_line = f.read(len(search_string))

    try:
        return last_line.decode() == search_string
    except UnicodeDecodeError:
        return False


class StoreLister(CommandProvider):
    def __call__(self, options: Namespace):
        for chris_plugin in self.find_chrispiled_plugins():
            print(chris_plugin)

    def find_chrispiled_plugins(self):
        bin_folder = path.expanduser(self.config.bin_folder)
        with os.scandir(bin_folder) as scan:
            return [f.name for f in scan if f.is_file() and is_product(f.path)]


class StoreRemover(CommandProvider):
    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)
        parser.add_argument('name',
                            help='executable name of the ChRIS plugin')

    def __call__(self, options: Namespace):
        bin_folder = path.expanduser(self.config.bin_folder)
        os.unlink(path.join(bin_folder, options.name))
