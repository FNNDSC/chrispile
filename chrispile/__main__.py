import argparse
import sys
from importlib.metadata import metadata
from .api import ChrispileApiCommand
from .run import ChrispileRunner
from .store import ChrispileInstaller, StoreLister, StoreRemover

program_info = metadata(__package__)


parser = argparse.ArgumentParser(description=program_info['summary'])


info_parser = parser.add_argument_group('info')
info_parser.add_argument('-V', '--version',
                    action='version',
                    version=f'%(prog)s {program_info["version"]}')

subparsers = parser.add_subparsers(title='subcommands')

run_parser = subparsers.add_parser('run',
                                   help='run a ChRIS plugin',
                                   usage='%(prog)s [--dry-run] [--reload-from] '
                                         '-- dock_image [args ...] inputdir/ outputdir/')
run = ChrispileRunner(run_parser)

api_parser = subparsers.add_parser('api', help='query the system for information')
api = ChrispileApiCommand(api_parser)

install_parser = subparsers.add_parser('install', help='install a ChRIS plugin as an executable')
installer = ChrispileInstaller(install_parser)

list_parser = subparsers.add_parser('list', help='list installed ChRIS plugins')
lister = StoreLister(list_parser)

uninstall_parser = subparsers.add_parser('uninstall', help='uninstall a ChRIS plugin')
uninstaller = StoreRemover(uninstall_parser)


def main():
    options = parser.parse_args()

    if 'func' not in vars(options):
        parser.print_usage()
        sys.exit(1)

    options.func(options)


if __name__ == '__main__':
    main()
