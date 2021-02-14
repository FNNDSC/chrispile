#!/bin/sh
# {{ selfexec }} {{ meta['type'] }} ChRIS plugin app
# Chrispile-generated wrapper script
#
# usage: {{ selfexec }} [--options ...] {{ './in/' if meta['type'] == FS }} ./out/
{% if linking == 'dynamic' -%}
# Environment variables:
#   CHRISPILE_DRY_RUN           if defined, print command and exit
{% set executor = 'run' -%}
{% macro chrispile_api(key) -%}
$({{ chrispile  }} api --as-flag {{ key }})
{%- endmacro -%}
{% set engine = chrispile_api('engine') -%}
{% set gpus = chrispile_api('gpu') -%}
{% set selinux_mount_flag = chrispile_api('selinux mount_flag') -%}
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
  injection+="-w / -v $source_folder:$resource_dir:ro{{ selinux_mount_flag }}"
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
    echo $@
  else
    exec $@
  fi
}
{% else -%}
{% set executor = 'exec' -%}
{% endif %}

{%- if meta['min_gpu_limit'] == 0 %}
{% set gpus = '' -%}
{% endif -%}

num_directories={{ 1 if meta['type'] == 'fs' else 2 }}

if [ "$#" -lt "$num_directories" ]; then
  num_directories=0
fi

# edge case: trying --help or --json on FS plugin
if [ "$#" = "1" ] && [[ "$1" = "-"* ]]; then
  num_directories=0
fi

# organize arguments into two arrays: one of cli_args, one of
# incoming/outgoing directories
for i in $(seq $(($#-$num_directories))); do
  cli_args[$i]=$1
  shift
done

for i in $(seq $num_directories); do
  directories[$i]=$1
  shift
done

# describe mount points
set -- /incoming:ro{{ selinux_mount_flag }} /outgoing:rw{{ selinux_mount_flag }}

# for FS plugin, there is no /incoming
until [ "$#" = "$num_directories" ]; do
  shift
done

# resolve mount points for host folders into container
for i in $(seq $num_directories); do
  real_dir="$(realpath -- ${directories[$i]})"
  if [ ! -d "$real_dir" ]; then
    echo "'$real_dir': No such directory"
    exit 1
  fi
  shared_volumes[$i]="-v $real_dir:$1"
  shift
done

set -- /incoming /outgoing

until [ "$#" = "$num_directories" ]; do
  shift
done

if [ -f /etc/localtime ]; then
  timezone="-v /etc/localtime:/etc/localtime:ro{{ selinux_mount_flag }}"
fi

{{ executor }} {{ engine }} run  \
    --rm --user $(id -u):$(id -g)  \
    {{ gpus }}  \
    $timezone ${shared_volumes[@]} $injection  \
    {{ dock_image }} {{ selfexec }}  \
    ${cli_args[@]} $@

# CHRISPILE {{ chrispile_uuid }}