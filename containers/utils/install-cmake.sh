#!/bin/sh
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Install the official Kitware CMake binary release into /opt/cmake-<version>-linux-<arch>
# and link it as /opt/cmake. The archive is verified against the sha256 recorded below.
set -eu

CMAKE_VERSION="${CMAKE_VERSION:-4.3.4}"
arch="$(uname -m)"

case "${CMAKE_VERSION}-${arch}" in
    4.3.4-x86_64)  sha256="ca6f08ccbd5e6b0a9068d33317d0d1aff7278d08cccaed4529b8fbead7942a68" ;;
    4.3.4-aarch64) sha256="56a8014a8f28b8ff9cbe2c6fa8beebc028ac5b1987195d122b847fb486dc5282" ;;
    *) echo "no sha256 known for cmake ${CMAKE_VERSION} on ${arch}" >&2; exit 2 ;;
esac

name="cmake-${CMAKE_VERSION}-linux-${arch}"
url="https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/${name}.tar.gz"

cd /tmp
curl -fsSL -o "${name}.tar.gz" "${url}"
echo "${sha256}  ${name}.tar.gz" | sha256sum -c -
tar -xzf "${name}.tar.gz" -C /opt
rm -f "${name}.tar.gz"
ln -sfn "/opt/${name}" /opt/cmake
/opt/cmake/bin/cmake --version
