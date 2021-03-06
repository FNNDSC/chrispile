import unittest
from unittest.mock import Mock
from tempfile import TemporaryDirectory
import argparse
import os
from os import path
import subprocess as sp

from chrispile.run import ChrispileRunner

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
        self.current_folder = os.getcwd()
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers()
        run_parser = self.subparsers.add_parser('run')
        self.runner = ChrispileRunner(run_parser)

    def tearDown(self):
        os.chdir(self.current_folder)

    def simulate(self, *args):
        """
        Run the program as if it were called from CLI.
        :param args: cli arguments
        """
        options = self.parser.parse_args(args)
        options.func(options)

    def simulate_output(self, *args) -> str:
        """
        Run the program as if it were called from the CLI,
        and return stdout as a string.
        :param args: cli arguments
        :return: output from stdout
        """
        self.runner.exec = Mock()
        self.simulate(*args)
        self.runner.exec.assert_called_once()
        cmd, code, env = self.runner.exec.call_args.args
        try:
            exe = sp.run(
                ['bash', '-s', '-'] + cmd,
                input=code, env=env, text=True, check=True,
                capture_output=True
            )
        except sp.CalledProcessError as e:
            self.fail(f'Command crashed: {str(cmd)} \n'
                      f'{e.output}')

        return exe.stdout

    def test_dry_run(self):
        with TemporaryDirectory() as outputdir:
            cmd = [
                'run', '--dry-run', '--',
                'fnndsc/pl-simpledsapp:2.0.0', '--dummyFloat', '3.5',
                self.inputdir, outputdir
            ]
            output = self.simulate_output(*cmd)
            self.assertTrue(
                output.startswith('docker run') or output.startswith('podman run'),
                'Dry-run output does not start with `docker/podman run`'
                'output: ' + output
            )
            self.assertEqual(
                0, len(os.listdir(outputdir)),
                'Did a dry-run but output directory is not empty'
            )

    def test_run_no_dirs(self):
        cmd = [
            'run', '--',
            'fnndsc/pl-simpledsapp:2.0.0', '--meta'
        ]
        output = self.simulate_output(*cmd)
        self.assertIn('TITLE: Simple chris ds app', output)

    def test_runs_container(self):
        cmd = ['fnndsc/pl-simpledsapp:2.0.0', '--dummyFloat', '3.5']
        with TemporaryDirectory() as outputdir:
            cmd += [self.inputdir, outputdir]
            self.simulate('run', '--', *cmd)
            files = os.listdir(outputdir)
            self.assertGreater(
                len(files), 0,
                'Output directory empty after running plugin'
            )
            a_file = path.join(outputdir, files[0])
            stat = os.stat(a_file)
            self.assertEqual(
                stat.st_uid, os.getuid(),
                'You do not own the file created by the plugin'
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

    def test_hot_reload(self):
        with TemporaryDirectory() as workspace:
            os.chdir(workspace)
            sp.run(['git', 'clone', 'https://github.com/FNNDSC/pl-simpledsapp.git'])
            os.chdir('pl-simpledsapp')
            sp.run(['git', 'checkout', '2.0.0'], stderr=sp.DEVNULL)
            src_folder = path.join(os.getcwd(), 'simpledsapp')
            with open(path.join(src_folder, 'simpledsapp.py'), 'at') as src:
                src.write('\n\n')
                src.write('    def run(self, options):\n')
                src.write('        print("these lines do not appear in the original source")\n')
                src.write('        with open(os.path.join(options.outputdir, "chrispile_test.txt"), "w") as f:\n')
                src.write('            f.write("we are testing chrispile")\n')

            with TemporaryDirectory() as outputdir:
                cmd = [
                    'run', '--reload-from', src_folder, '--',
                    'fnndsc/pl-simpledsapp:2.0.0', '--dummyFloat', '3.5',
                    self.inputdir, outputdir
                ]

                output = self.simulate_output(*cmd)

                self.assertIn('these lines do not appear in the original source', output)
                output_file = path.join(outputdir, 'chrispile_test.txt')
                self.assertTrue(
                    path.isfile(output_file),
                    'Modified source code of pl-simpledsapp did not produce the hard-coded output file.'
                )
                with open(output_file, 'r') as f:
                    output_content = f.readlines()
                self.assertEqual(
                    'we are testing chrispile', output_content[0],
                    'Unexpected content in output from modified pl-simpledsapp'
                )


if __name__ == '__main__':
    unittest.main()
