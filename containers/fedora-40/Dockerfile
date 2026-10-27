# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Build image for the AlmaLinux 9 (el9) rpm, built with fedpkg/mock.
# Taken over from sil-kit-docker-build containers/packaging-fedora.
# mock needs the container to run with --privileged.

# fedora:40
FROM docker.io/library/fedora@sha256:3c86d25fef9d2001712bc3d9b091fc40cf04be4767e48f1aa3b785bf58d300ed

RUN dnf -y install \
      fedora-packager \
      fedora-review \
      git \
&&  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n' | sort > /etc/sil-kit-pkg-image-packages.txt \
&&  dnf clean all

# Link the AlmaLinux 9 + EPEL mock config as epel-9
RUN mkdir -p ~/.config/mock \
&&  ln -sf /etc/mock/alma+epel-9-x86_64.cfg ~/.config/mock/epel-9-x86_64.cfg
