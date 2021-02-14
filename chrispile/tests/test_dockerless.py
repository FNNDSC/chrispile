import unittest
import os
from tempfile import TemporaryDirectory

from chrispile.render import Chrispiler
from chrispile.config import ChrispileConfig

from .dockercli import DockerCli


class TestWithoutDocker(unittest.TestCase):
    def setUp(self):
        # disable docker
        self.tempdir = TemporaryDirectory()
        overdir = self.tempdir.name
        os.environ['PATH'] = ':'.join([overdir, os.environ['PATH']])
        os.symlink('/bin/false', os.path.join(overdir, 'docker'))

        self.config = ChrispileConfig({'engine': 'podman'})
        DockerCli('podman').pull_if_needed('fnndsc/pl-simpledsapp:2.0.0')

    def tearDown(self):
        self.tempdir.cleanup()

    def test_only_podman(self):
        self.compiler = Chrispiler(self.config)
        self.compiler.compile_plugin('fnndsc/pl-simpledsapp:2.0.0', linking='static')


if __name__ == '__main__':
    unittest.main()
