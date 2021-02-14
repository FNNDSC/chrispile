import unittest

from chrispile.config import ChrispileConfig
from chrispile.render import Chrispiler

from .dockercli import DockerCli


class TestRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = Chrispiler(ChrispileConfig())
        DockerCli().pull_if_needed('fnndsc/pl-simpledsapp:2.0.0')

    def test_image_not_pulled(self):
        with self.assertRaises(SystemExit):
            self.compiler.test_the_waters('fnndsc/pl-whatisversioning:dne')

    def test_static_linking(self):
        code = self.compiler.compile_plugin('fnndsc/pl-simpledsapp:2.0.0', linking='static')
        self.assertNotIn('chrispile api ', code)

    def test_resource_dir(self):
        lib_folder = '/usr/local/lib/python3.9/site-packages/simpledsapp'
        code = self.compiler.compile_plugin('fnndsc/pl-simpledsapp:2.0.0', linking='static')
        self.assertNotIn(lib_folder, code)
        code = self.compiler.compile_plugin('fnndsc/pl-simpledsapp:2.0.0', linking='dynamic')
        self.assertIn(lib_folder, code)

    def test_selinux_volumes(self):
        code = self.compiler.compile_plugin('fnndsc/pl-simpledsapp:2.0.0', linking='static')
        self.assertNotIn('/incoming:ro,z', code)
        self.assertNotIn('/outgoing:rw,z', code)

        selinux_config = ChrispileConfig({'selinux': 'enforcing'})
        compiler = Chrispiler(selinux_config)
        code = compiler.compile_plugin('fnndsc/pl-simpledsapp:2.0.0', linking='static')
        self.assertIn('/incoming:ro,z', code)
        self.assertIn('/outgoing:rw,z', code)


if __name__ == '__main__':
    unittest.main()
