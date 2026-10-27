# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Build image for the Ubuntu 22.04 packages (arm64 .deb, built natively on an arm64 runner).
# Package list follows ptv/docker-images dockerfiles/sil-kit-build/ubuntu-2204.
# The base image is pinned by digest and apt reads from a fixed snapshot.ubuntu.com
# timestamp, so a rebuild of this image installs the same package versions.

# ubuntu:22.04
FROM docker.io/library/ubuntu@sha256:e0f80c829509ef4df9e76bd8944eb7b8ec25cbb379b112a7f9448b2c77a77c9b

ARG UBUNTU_SNAPSHOT=20261020T000000Z
ARG CMAKE_VERSION=4.3.4

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

COPY --from=utils install-cmake.sh /tmp/install-cmake.sh

# snapshot.ubuntu.com is served over https only, so ca-certificates comes from the
# regular archive first.
RUN apt-get update \
&&  apt-get install --no-install-recommends --no-install-suggests -y ca-certificates \
&&  sed -i -E \
        -e "s#http://(archive|security)\.ubuntu\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#" \
        -e "s#http://ports\.ubuntu\.com/ubuntu-ports/?#https://snapshot.ubuntu.com/ubuntu-ports/${UBUNTU_SNAPSHOT}/#" \
        /etc/apt/sources.list \
&&  apt-get update \
&&  apt-get install --no-install-recommends --no-install-suggests -y \
      binutils \
      build-essential \
      ca-certificates \
      clang \
      curl \
      debhelper \
      devscripts \
      dh-make \
      dpkg-dev \
      doxygen \
      dwz \
      g++ \
      gcc \
      git \
      gpg-agent \
      locales \
      ninja-build \
      python3 \
      python3-pip \
      python3-venv \
      software-properties-common \
      tzdata \
      wget \
      zip \
&&  sh /tmp/install-cmake.sh \
&&  dpkg-query -W -f '${Package} ${Version}\n' > /etc/sil-kit-pkg-image-packages.txt \
&&  apt-get clean \
&&  rm -rf /var/lib/apt/lists/* /tmp/install-cmake.sh

ENV PATH="/opt/cmake/bin:${PATH}"
