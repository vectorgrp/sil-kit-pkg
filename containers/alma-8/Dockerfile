# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Build image for the AlmaLinux 8 (el8) tarball.
# Toolchain: gcc-toolset-12 (gcc 12). Binaries built with it only need the system
# libstdc++ of el8, the newer parts are linked statically by the toolset.
# The base image is pinned by digest. AlmaLinux 8.10 repositories still receive
# updates, so the installed versions are recorded in /etc/sil-kit-pkg-image-packages.txt;
# reproducibility of the packages comes from pinning this image by digest.

# almalinux:8
FROM docker.io/library/almalinux@sha256:8b469a3a78515e8a18ea8fc727e6a3679e1d0c5ba6f58d5b30be3d0d9b86cffe

ARG CMAKE_VERSION=4.3.4

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY --from=utils install-cmake.sh /tmp/install-cmake.sh

RUN dnf install -y dnf-plugins-core \
&&  dnf config-manager --set-enabled powertools \
&&  dnf install -y \
      binutils \
      file \
      gcc-toolset-12-binutils \
      gcc-toolset-12-dwz \
      gcc-toolset-12-gcc \
      gcc-toolset-12-gcc-c++ \
      git \
      make \
      ninja-build \
      python39 \
      tar \
      unzip \
      which \
      xz \
&&  sh /tmp/install-cmake.sh \
&&  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n' | sort > /etc/sil-kit-pkg-image-packages.txt \
&&  dnf clean all \
&&  rm -rf /var/cache/dnf /tmp/install-cmake.sh

ENV PATH="/opt/rh/gcc-toolset-12/root/usr/bin:/opt/cmake/bin:${PATH}"
ENV CC=/opt/rh/gcc-toolset-12/root/usr/bin/gcc
ENV CXX=/opt/rh/gcc-toolset-12/root/usr/bin/g++
