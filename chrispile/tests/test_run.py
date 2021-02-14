import unittest
from unittest.mock import Mock
from tempfile import TemporaryDirectory
import argparse
import os
from os import path
import subprocess as sp

from chrispile.run import ChrispileRunner
from chrispile.config import ChrispileConfig

from .dockercli import DockerCli


class TestRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = TemporaryDirectory()
        cls.inputdir = cls.td.name
        example_files = ['a', 'b', 'c']
        for i, fn in enumerate(example_files):
            with open(path.join(cls.inputdir, fn), 'w') as f:
                f.write(str(i))
        DockerCli().pull_if_needed('fnndsc/pl-simpledsapp:2.0.0')

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def setUp(self):
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers()
        run_parser = self.subparsers.add_parser('run')
        self.runner = ChrispileRunner(run_parser)
        self.runner.config = ChrispileConfig({'engine': 'docker'})

    def simulate(self, *args):
        options = self.parser.parse_args(args)
        options.func(options)

    def simulate_output(self, *args):
        self.runner.exec = Mock()
        self.simulate('run', '--dry-run', '--', *args)
        self.runner.exec.assert_called_once()
        cmd, code, env = self.runner.exec.call_args.args
        exe = sp.run(
            ['sh', '-s', '-'] + cmd,
            input=code, env=env, text=True, check=True,
            capture_output=True
        )
        return exe.stdout

    def test_dry_run(self):
        cmd = ['fnndsc/pl-simpledsapp:2.0.0', '--dummyFloat', '3.5']
        with TemporaryDirectory() as outputdir:
            cmd += [self.inputdir, outputdir]
            output = self.simulate_output(*cmd)
            self.assertTrue(output.startswith('docker run'))
            self.assertEqual(
                0, len(os.listdir(outputdir)),
                'did a dry run but output directory is not empty'
            )

    def test_run_no_dirs(self):
        cmd = ['fnndsc/pl-simpledsapp:2.0.0', '--meta']
        output = self.simulate_output(*cmd)
        self.assertIn('simpledsapp', output)

    def test_runs_container(self):
        cmd = ['fnndsc/pl-simpledsapp:2.0.0', '--dummyFloat', '3.5']
        with TemporaryDirectory() as outputdir:
            cmd += [self.inputdir, outputdir]
            self.simulate('run', '--', *cmd)
            files = os.listdir(outputdir)
            self.assertGreater(
                len(files), 0,
                'output directory empty after running plugin'
            )
            a_file = path.join(outputdir, files[0])
            stat = os.stat(a_file)
            self.assertEqual(
                stat.st_uid, os.getuid(),
                'you do not own the file created by the plugin'
            )
            os.unlink(a_file)

    def test_exits_with_code(self):
        with self.assertRaises(SystemExit) as exit_condition:
            self.runner.exec(
                ['some', 'option'],
                '#!/bin/sh\nexit 37',
                {}
            )
        self.assertEqual(exit_condition.exception.code, 37)


if __name__ == '__main__':
    unittest.main()
