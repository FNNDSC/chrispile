import subprocess as sp

from chrispile.api import EngineEndpoint
from chrispile.config import get_config


class DockerCli:
    def __init__(self, engine=None):
        config = get_config()
        self.engine = engine if engine else EngineEndpoint(config).as_shell()

    def pull_if_needed(self, dock_image: str):
        image_id = sp.check_output([self.engine, 'images', '--format', '{{ .ID}}', dock_image])
        if not image_id:
            sp.run([self.engine, 'pull', dock_image])

    def docker_tag(self, dock_image: str, new_tag: str):
        sp.run([self.engine, 'tag', dock_image, new_tag])

    def docker_rmi(self, dock_image: str):
        sp.run([self.engine, 'rmi', dock_image])
