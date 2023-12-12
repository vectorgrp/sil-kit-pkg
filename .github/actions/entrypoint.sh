#!/bin/bash

runner_uid=$(id -u)
runner_gid=$(id -g)

echo "Runner UID: ${runner_uid}"
echo "Runner GID: ${runner_gid}"

useradd --uid "${runner_uid}" --no-user-group --home-dir "$(pwd)" --no-create-home worker

sudo -E -u worker -- "$@"

