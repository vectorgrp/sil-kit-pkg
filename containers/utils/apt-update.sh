#!/bin/sh
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# apt-get update that fails when any index file could not be downloaded, and retries.
# apt only warns about failed index downloads ("W: Failed to fetch ...") and then works
# with an incomplete package list, so a later apt-get install fails with a misleading
# "Unable to locate package". snapshot.ubuntu.com often answers single requests with
# 500/503; already downloaded indexes are kept between attempts.
# Also enables apt's own retries for the package downloads that follow.
set -eu

attempts="${APT_UPDATE_ATTEMPTS:-6}"
log=/tmp/apt-update.log

echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/80-sil-kit-pkg-retries

i=1
while :; do
    rc=0
    apt-get update > "${log}" 2>&1 || rc=$?
    cat "${log}"
    if [ "${rc}" -eq 0 ] && ! grep -Eq '^(W|E): (Failed to fetch|Some index files failed)' "${log}"; then
        rm -f "${log}"
        exit 0
    fi
    if [ "${i}" -ge "${attempts}" ]; then
        echo "apt-get update: index files still missing after ${attempts} attempts" >&2
        exit 1
    fi
    delay=$((i * 15))
    echo "apt-get update: index files missing (attempt ${i}/${attempts}), retrying in ${delay}s" >&2
    sleep "${delay}"
    i=$((i + 1))
done
