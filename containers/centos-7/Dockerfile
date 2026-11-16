# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Build image for the CentOS 7 (el7) tarball.
# CentOS 7 is EOL: all repositories point to vault.centos.org, which no longer changes.
# Toolchain: devtoolset-11 (gcc 11). Binaries built with it only need the system
# libstdc++ of CentOS 7, the newer parts are linked statically by the toolset.
# Python: rh-python38, the packaging scripts need Python 3.7 or newer.

# centos:7
FROM docker.io/library/centos@sha256:be65f488b7764ad3638f236b7b515b3678369a5124c47b8d32916d6487418ea4

ARG CMAKE_VERSION=4.3.4
ARG NINJA_VERSION=1.13.2

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8

COPY --from=utils install-cmake.sh /tmp/install-cmake.sh
COPY --from=utils install-ninja.sh /tmp/install-ninja.sh

RUN sed -i -e 's/^mirrorlist=/#mirrorlist=/' \
           -e 's|^#\?baseurl=http://mirror.centos.org/centos/\$releasever|baseurl=https://vault.centos.org/7.9.2009|' \
           /etc/yum.repos.d/CentOS-*.repo \
&&  yum install -y centos-release-scl \
&&  sed -i -e 's/^mirrorlist=/#mirrorlist=/' \
           -e 's|^#\?\s*baseurl=http://mirror.centos.org/centos/7/sclo/|baseurl=https://vault.centos.org/7.9.2009/sclo/|' \
           /etc/yum.repos.d/CentOS-SCLo-*.repo \
&&  yum install -y \
      binutils \
      curl \
      devtoolset-11-binutils \
      devtoolset-11-dwz \
      devtoolset-11-gcc \
      devtoolset-11-gcc-c++ \
      file \
      git \
      make \
      rh-python38-python \
      tar \
      unzip \
      which \
      xz \
&&  sh /tmp/install-cmake.sh \
&&  sh /tmp/install-ninja.sh \
&&  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n' | sort > /etc/sil-kit-pkg-image-packages.txt \
&&  yum clean all \
&&  rm -rf /var/cache/yum /tmp/install-*.sh

ENV PATH="/opt/rh/devtoolset-11/root/usr/bin:/opt/rh/rh-python38/root/usr/bin:/opt/cmake/bin:${PATH}"
ENV LD_LIBRARY_PATH="/opt/rh/devtoolset-11/root/usr/lib64:/opt/rh/devtoolset-11/root/usr/lib:/opt/rh/rh-python38/root/usr/lib64"
ENV CC=/opt/rh/devtoolset-11/root/usr/bin/gcc
ENV CXX=/opt/rh/devtoolset-11/root/usr/bin/g++
