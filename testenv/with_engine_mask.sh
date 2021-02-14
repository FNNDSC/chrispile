#!/bin/bash
# Run a command with container engines masked
# usage: ENGINE_TO_TEST=podman testenv/with_engine_mask.sh python -m unittest

ENGINES=(docker podman)

mask_dir=$(mktemp -d)

export PATH=$mask_dir:$PATH

for engine in "${ENGINES[@]}"; do
  if [ "$engine" != "$ENGINE_TO_TEST" ]; then
    ln -sv /bin/false $mask_dir/$engine
  fi
done

source_dir=$(dirname "$(readlink -f "$0")")
CHRISPILE_CONFIG_FILE=$source_dir/$ENGINE_TO_TEST.yml

if [ -f "$CHRISPILE_CONFIG_FILE" ]; then
  export CHRISPILE_CONFIG_FILE
fi

$@
result=$?

rm -rv $mask_dir
exit $result
