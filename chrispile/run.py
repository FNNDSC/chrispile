import os
import sys
import subprocess as sp
from argparse import ArgumentParser, Namespace

from .util import CommandProvider
from .render import Chrispiler


class ChrispileRunner(CommandProvider):
    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)
        parser.add_argument('-d', '--dry-run',
                            action='store_true',
                            help='print command to run without running it')
        parser.add_argument('-e', '--reload-from',
                            metavar='src',
                            help='mount given host directory as source folder for '
                                 'rapid development')
        parser.add_argument('dock_image',
                            help='container image of the ChRIS plugin')
        parser.add_argument('args',
                            nargs='*',
                            help='arguments to pass to the ChRIS plugin')

    def __call__(self, options: Namespace):
        env = {}
        env.update(os.environ)
        if options.dry_run:
            env['CHRISPILE_DRY_RUN'] = 'y'
        if options.reload_from:
            env['CHRISPILE_HOST_SOURCE_DIR'] = options.reload_from

        compiler = Chrispiler(self.config)
        compiler.test_the_waters(options.dock_image)
        code = compiler.compile_plugin(options.dock_image)

        self.exec(options.args, code, env)

    @staticmethod
    def exec(args, code, env):
        try:
            sp.run(['bash', '-s', '-'] + args, input=code, env=env, text=True, check=True)
        except sp.CalledProcessError as e:
            sys.exit(e.returncode)
