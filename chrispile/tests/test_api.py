import unittest
import sys

from chrispile.api import SubShellApi, ShellBuilderApi
from chrispile.config import ChrispileConfig


class MyTestCase(unittest.TestCase):
    PROGRAM_NAME = sys.argv[0]

    def test_subshell(self):
        api = SubShellApi()
        self.assertEqual(api.gpu(), f'$({self.PROGRAM_NAME} api gpu)')
        self.assertEqual(api.gpu(['is', 'fun']), f'$({self.PROGRAM_NAME} api gpu is fun)')

    def test_gpu_with_selinux(self):
        config = ChrispileConfig(gpu='nvidia-container-toolkit', selinux='enforcing')
        result = ShellBuilderApi(config).gpu()
        self.assertIn('--security-opt label=type:nvidia_container_t', result)


if __name__ == '__main__':
    unittest.main()
