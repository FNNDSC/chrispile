#!/bin/bash
# Run a command with container engines masked
# usage: ENGINE_TO_TEST=podman test/with_engine_mask.sh python -m unittest

ENGINES=(docker podman)

mask_dir=$(mktemp -d)

export PATH=$mask_dir:$PATH

for engine in "${ENGINES[@]}"; do
  if [ "$engine" != "$ENGINE_TO_TEST" ]; then
    ln -sv /bin/false $mask_dir/$engine
  fi
done

export CHRISPILE_CONFIG_FILE=$mask_dir/chrispile_config.yml
echo "engine: $ENGINE_TO_TEST" > $CHRISPILE_CONFIG_FILE

$@
result=$?

rm -rv $mask_dir
exit $result
