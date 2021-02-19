import unittest

from chrispile.api import ShellBuilderApi
from chrispile.render import SubShellApi
from chrispile.config import ChrispileConfig


class MyTestCase(unittest.TestCase):
    def test_subshell(self):
        api = SubShellApi()
        self.assertEqual(api.gpu(), f'$(chrispile api --as-flag gpu)')
        self.assertEqual(api.gpu('is', 'fun'), f'$(chrispile api --as-flag gpu is fun)')

    def test_gpu_with_selinux(self):
        config = ChrispileConfig(gpu='nvidia-container-toolkit', selinux='enforcing')
        result = ShellBuilderApi(config).gpu()
        self.assertIn('--security-opt label=type:nvidia_container_t', result)



if __name__ == '__main__':
    unittest.main()
