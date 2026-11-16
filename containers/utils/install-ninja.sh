#!/bin/sh
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Install ninja from the official PyPI wheel (manylinux2014, runs on glibc 2.17).
# The release binary on GitHub needs GLIBCXX_3.4.21 and does not run on CentOS 7.
set -eu

NINJA_VERSION="${NINJA_VERSION:-1.13.2}"

case "${NINJA_VERSION}-$(uname -m)" in
    1.13.2-x86_64) sha256="65a24341b5ac09fcadcc37082660be40a94174e51a937fabf6e2cae26225fa2c" ;;
    *) echo "no sha256 known for ninja ${NINJA_VERSION} on $(uname -m)" >&2; exit 2 ;;
esac

wheel="ninja-${NINJA_VERSION}-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"

cd /tmp
curl -fsSL -o "${wheel}" "https://files.pythonhosted.org/packages/py3/n/ninja/${wheel}"
echo "${sha256}  ${wheel}" | sha256sum -c -
unzip -o -j "${wheel}" "ninja-${NINJA_VERSION}.data/scripts/ninja" -d /usr/local/bin
chmod 0755 /usr/local/bin/ninja
rm -f "${wheel}"
ninja --version
