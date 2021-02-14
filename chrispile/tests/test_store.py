import unittest
from tempfile import TemporaryDirectory, NamedTemporaryFile
import argparse
from os import path

from chrispile.store import is_product, ChrispileInstaller, StoreRemover
from chrispile.config import ChrispileConfig

from .sample import pull_if_needed


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.dir = self.tempdir.name
        self.config = ChrispileConfig({'bin_folder': self.dir})

        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers()
        install_parser = self.subparsers.add_parser('install')
        installer = ChrispileInstaller(install_parser)
        installer.config = self.config
        uninstall_parser = self.subparsers.add_parser('uninstall')
        remover = StoreRemover(uninstall_parser)
        remover.config = self.config

        self.example_image = 'fnndsc/pl-simpledsapp:2.0.0'
        pull_if_needed(self.example_image)

    def tearDown(self):
        self.tempdir.cleanup()

    def simulate(self, *args):
        options = self.parser.parse_args(args)
        options.func(options)

    def install_to_file(self, name=None):
        if name:
            target = path.join(self.dir, name)
        else:
            # just to get a random name
            with NamedTemporaryFile(dir=self.dir, delete=True) as tmp:
                pass
            target = tmp.name
        self.simulate('install', '-o', target, self.example_image)
        return target

    def test_can_recognize_product(self):
        target = self.install_to_file()
        self.assertTrue(is_product(target))

    def test_is_not_product(self):
        self.assertFalse(is_product('/bin/ls'))

    def test_uninstall(self):
        name = 'uninstall_me'
        target = self.install_to_file(name)
        self.assertTrue(path.exists(target))
        self.simulate('uninstall', name)
        self.assertFalse(path.exists(target))


if __name__ == '__main__':
    unittest.main()
