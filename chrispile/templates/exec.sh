#!/usr/bin/env bash
# {{ selfexec }} {{ meta['type'] }} ChRIS plugin app
# Chrispile-generated wrapper script
#
# usage: {{ selfexec }} [--options ...] {{ './in/' if meta['type'] != 'fs' }} ./out/
{% if linking == 'dynamic' -%}
{% set executor = 'run' -%}
{% set api = SubShellApi -%}
{% else -%}
{% set executor = 'exec' %}
{% set api = ShellBuilderApi -%}
{% endif -%}
{% set engine = api.engine() -%}
{% set gpus = api.gpu() -%}
{% set selinux_mount_flag = api.selinux('mount_flag') -%}
{% if linking == 'dynamic' -%}
# Environment variables:
#   CHRISPILE_DRY_RUN           if defined, print command and exit
{% set resource_dir = info.find_resource_dir(dock_image, meta) -%}
{% if resource_dir.startswith('/') -%}
#   CHRISPILE_HOST_SOURCE_DIR   if non-empty, mount it into the container

# installation directory of the python package
{# e.g. /usr/local/lib/python3.9/site-packages/acoolpackage} -#}
resource_dir={{ resource_dir }}

if [ -n "$CHRISPILE_HOST_SOURCE_DIR" ]; then
  source_folder="$(realpath -- "$CHRISPILE_HOST_SOURCE_DIR")"
  if [ ! -d "$source_folder" ]; then
    echo "'$source_folder': No such directory"
    exit 1
  fi
  if [ ! -f "$source_folder/__init__.py" ]; then
    echo "'$source_folder/__init__.py': No such file"
    exit 1
  fi
  resource_injection="-w / -v $source_folder:$resource_dir:ro{{ selinux_mount_flag }}"
fi
{% else %}
if [ -n "$CHRISPILE_HOST_SOURCE_DIR" ]; then
  echo "Could not locate package installation directory within container image."
  echo "Your ChRIS plugin was not built with the code being installed properly using pip."
  echo "To take advantage of the --dry-run feature, please modernize your Dockerfile."
  exit 1
fi
{% endif %}

function run () {
  if [ -v CHRISPILE_DRY_RUN ]; then
    echo "$@"
  else
    exec "$@"
  fi
}

{#- user detection should be a candidate for deprecation #}
{# when eventually rootless containers become mainstream #}
# detect cgroup v2 rootless support
# using podman? what a cool kid, we're assuming id mapping is configured
if [ "{{ engine }}" = "docker" ]; then
{% include 'rootless_docker.sh' %}
fi
{% else -%}
{%- if engine == 'docker' %}
# set container user if cgroup v2 is unsupported
{% include 'rootless_docker.sh' %}
{%- endif %}
{% endif %}

{%- if meta['min_gpu_limit'] == 0 %}
{% set gpus = '' -%}
{% endif -%}


{% include 'mounts.sh' %}

if [ -f /etc/localtime ]; then
  timezone="-v /etc/localtime:/etc/localtime:ro{{ selinux_mount_flag }}"
fi

{{ executor }} {{ engine }} run               \
    --rm {{ gpus }} $user_setting $timezone   \
    ${shared_volumes[@]} $resource_injection  \
    {{ dock_image }} {{ selfexec }}  \
    "${cli_args[@]}"

# CHRISPILE {{ chrispile_uuid }}