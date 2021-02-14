import subprocess as sp

from chrispile.api import EngineEndpoint
from chrispile.config import ChrispileConfig

ENGINE = EngineEndpoint(ChrispileConfig()).as_shell()


def pull_if_needed(dock_image: str):
    image_id = sp.check_output([ENGINE, 'images', '--format', '{{ .ID}}', dock_image])
    if not image_id:
        sp.run([ENGINE, 'pull', dock_image])


def docker_tag(dock_image: str, new_tag: str):
    sp.run([ENGINE, 'tag', dock_image, new_tag])


def docker_rmi(dock_image: str):
    sp.run([ENGINE, 'rmi', dock_image])
