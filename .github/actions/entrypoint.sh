#!/bin/bash

runner_uid=$(ls -lnd . | awk '{ print $3; }')
runner_gid=$(ls -lnd . | awk '{ print $4; }')
echo "Runner UID: ${runner_uid}"
echo "Runner GID: ${runner_gid}"

useradd --uid "${runner_uid}" --no-user-group --home-dir "$(pwd)" --no-create-home worker

sudo -E -u worker -- "$@"

