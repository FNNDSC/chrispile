import subprocess as sp


def pull_if_needed(dock_image: str):
    image_id = sp.check_output(['docker', 'images', '--format', '{{ .ID}}', dock_image])
    if not image_id:
        sp.run(['docker', 'pull', dock_image])


def docker_tag(dock_image: str, new_tag: str):
    sp.run(['docker', 'tag', dock_image, new_tag])


def docker_rmi(dock_image: str):
    sp.run(['docker', 'rmi', dock_image])
