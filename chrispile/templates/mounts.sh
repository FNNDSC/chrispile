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
