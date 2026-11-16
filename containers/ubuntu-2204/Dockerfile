# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Build image for the Ubuntu 22.04 packages (arm64 .deb, built natively on an arm64 runner).
# Package list follows ptv/docker-images dockerfiles/sil-kit-build/ubuntu-2204.
# The base image is pinned by digest, apt reads the regular Ubuntu ports archive
# (snapshot.ubuntu.com has no ubuntu-ports). A rebuild of this image can therefore
# install newer package versions; the installed versions are recorded in
# /etc/sil-kit-pkg-image-packages.txt, and reproducibility of the packages comes
# from pinning this image by digest in release/packages.json.

# ubuntu:22.04
FROM docker.io/library/ubuntu@sha256:e0f80c829509ef4df9e76bd8944eb7b8ec25cbb379b112a7f9448b2c77a77c9b

ARG CMAKE_VERSION=4.3.4

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

COPY --from=utils install-cmake.sh /tmp/install-cmake.sh

RUN apt-get update \
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
