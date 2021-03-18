num_directories={{ 1 if meta['type'] == 'fs' else 2 }}

# user did not give enough options to successfully run the program,
# assume they are trying to run --version, --json, or --meta
if [ "$#" -lt "$num_directories" ]; then
  num_directories=0
fi

# edge case: trying --help or --json on FS plugin
if [ "$#" = "1" ] && [[ "$1" = "-"* ]]; then
  num_directories=0
fi

# organize arguments into two arrays: one of cli_args, one of
# incoming/outgoing directories

{%- raw %}
function append_args () {
  until [ "$#" = "0" ]; do
    cli_args[${#cli_args[@]}]="$1"
    shift
  done
}

# simple polyfill for seq which outputs nothing for input less than 1
#
# BSD seq behaves oddly with 0 or negative numbers
# $ seq 0
# 1
# 0
# wtf is that?
function seq () {
  if [ "$1" -lt "1" ]; then
    return
  fi
  command seq $1
}
{% endraw %}

num_cli_args=$(($# - $num_directories))
for i in $(seq $num_cli_args); do
  append_args $1
  shift
done

for i in $(seq $num_directories); do
  directories[$i]=$1
  shift
done


# describe mount points
case $num_directories in
  # we have a dummy string '/nil' so that the array is one-indexed
  # makes it easier to use seq and for loops
  0) mount_points=( /nil ) ;;
  1) mount_points=( /nil /outgoing:rw{{ selinux_mount_flag }} )
     append_args /outgoing ;;
  2) mount_points=( /nil /incoming:ro{{ selinux_mount_flag }} /outgoing:rw{{ selinux_mount_flag }} )
     append_args /incoming /outgoing ;;
esac

# resolve mount points for host folders into container
for i in $(seq $num_directories); do
  real_dir="$(realpath -- ${directories[$i]})"
  if [ ! -d "$real_dir" ]; then
    echo "'$real_dir': No such directory"
    exit 1
  fi
  shared_volumes[$i]="-v $real_dir:${mount_points[$i]}"
done
