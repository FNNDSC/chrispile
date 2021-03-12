{# TODO -#}
{# user namespace remapping without cgroup v2 -#}
{# docker before v20.10 does not have info .CgroupVersion -#}
{% raw -%}
if [ "$(docker info --format '{{ .CgroupVersion }}' 2> /dev/null)" != "2" ]; then
  user_setting="--userns=host --user $(id -u):$(id -g)"
fi
{%- endraw %}