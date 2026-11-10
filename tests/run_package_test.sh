#!/bin/sh
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Smoke test a package inside a plain distribution container (no build image).
# Installs a compiler, cmake and ninja, then runs test_deb.py.
#
# Usage (from the sil-kit-pkg checkout): tests/run_package_test.sh <deb|rpm|tgz> <package-dir>
set -eu

format="$1"
package_dir="$2"
here="$(cd "$(dirname "$0")" && pwd)"
utils="${here}/../containers/utils"

. /etc/os-release
major="${VERSION_ID%%.*}"

case "${ID}-${major}" in
    ubuntu-*)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y --no-install-recommends ca-certificates curl g++ ninja-build python3
        sh "${utils}/install-cmake.sh"
        export CC=gcc CXX=g++
        ;;
    centos-7)
        sed -i -e 's/^mirrorlist=/#mirrorlist=/' \
               -e 's|^#\?baseurl=http://mirror.centos.org/centos/\$releasever|baseurl=https://vault.centos.org/7.9.2009|' \
               /etc/yum.repos.d/CentOS-*.repo
        yum install -y centos-release-scl
        sed -i -e 's/^mirrorlist=/#mirrorlist=/' \
               -e 's|^#\?\s*baseurl=http://mirror.centos.org/centos/7/sclo/|baseurl=https://vault.centos.org/7.9.2009/sclo/|' \
               /etc/yum.repos.d/CentOS-SCLo-*.repo
        yum install -y curl devtoolset-11-gcc-c++ python3 unzip
        sh "${utils}/install-cmake.sh"
        sh "${utils}/install-ninja.sh"
        export CC=/opt/rh/devtoolset-11/root/usr/bin/gcc CXX=/opt/rh/devtoolset-11/root/usr/bin/g++
        ;;
    almalinux-8)
        dnf install -y dnf-plugins-core
        dnf config-manager --set-enabled powertools
        dnf install -y gcc-c++ ninja-build python3 tar
        sh "${utils}/install-cmake.sh"
        export CC=gcc CXX=g++
        ;;
    almalinux-9|fedora-*)
        dnf install -y dnf-plugins-core
        dnf config-manager --set-enabled crb || true
        dnf install -y clang ninja-build python3 tar
        sh "${utils}/install-cmake.sh"
        export CC=clang CXX=clang++
        ;;
    *)
        echo "unsupported test distribution ${ID} ${VERSION_ID}" >&2
        exit 64
        ;;
esac

export PATH="/opt/cmake/bin:${PATH}"

case "${ID}" in
    ubuntu) distro=ubuntu ;;
    fedora|almalinux) [ "${format}" = rpm ] && distro=fedora || distro="${ID}" ;;
    *) distro="${ID}" ;;
esac

python3 "${here}/test_deb.py" \
    --package-format "${format}" \
    --package-directory "${package_dir}" \
    --test-directory "${here}" \
    --distro "${distro}" \
    --distro-version "${major}"
