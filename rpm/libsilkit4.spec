Name:       libsilkit4
Version:    4.0.54
Release:    %autorelease
Summary:    The SIL Framework from Vector
License:    MIT
URL:        https://github.com/vectorgrp/sil-kit
Source0:    libsilkit-%{version}.tar.gz
Source1:    sil-kit-registry.service
BuildRequires: clang
BuildRequires: ninja-build
BuildRequires: cmake
BuildRequires: lld
BuildRequires: systemd-rpm-macros

%description
An open-source library for connecting Software-in-the-Loop Environments

%package devel
Summary: Develop Files for the libsilkit package

%description devel
The development headers and CMake files for libsilkit

%package utils
Summary: SilKit Util Binaries

%description utils
Utility programs for libsilkit. Includes
* sil-kit-monitor
* sil-kit-registry
* sil-kit-system-controller

%prep
%setup -q

%build
%global toolchain clang
%define __builder ninja
%cmake  -DSILKIT_INSTALL_SOURCE=Off -DSILKIT_BUILD_LINUX_PACKAGE=On \\\
        -S . \\\
        -GNinja \\\
        -DCMAKE_EXE_LINKER_FLAGS="${CMAKE_EXE_LINKER_FLAGS} -Wl,--undefined-version -fuse-ld=lld -Wl,--build-id=sha1 -pie" \\\
        -DCMAKE_MODULE_LINKER_FLAGS="${CMAKE_MODULE_LINKER_FLAGS} -Wl,--undefined-version -fuse-ld=lld -Wl,--build-id=sha1" \\\
        -DCMAKE_SHARED_LINKER_FLAGS="${CMAKE_SHARED_LINKER_FLAGS} -Wl,--as-needed -Wl,--no-undefined -Wl,-z,now -Wl,--undefined-version -fuse-ld=lld -Wl,--build-id=sha1" \\\
        -DBUILD_SHARED_LIBS:BOOL=OFF

%cmake_build --parallel %_smp_mflags

%install
%cmake_install

install -d -m 0750 %{buildroot}/%{_unitdir}
install -p -D -m 0644 %{SOURCE1} %{buildroot}/%{_unitdir}/

%check
%ctest

%files
%{_libdir}/libSilKit.so.%{version}
%{_libdir}/libSilKit.so.4

%files devel
%{_libdir}/libSilKit.so
%{_libdir}/cmake/*
%{_includedir}/*

%files utils
%{_bindir}/sil-kit-monitor
%{_bindir}/sil-kit-registry
%{_bindir}/sil-kit-system-controller
%{_mandir}/man1/*.1.gz
%{_unitdir}/sil-kit-registry.service

%changelog

* Mon Nov 11 2024 Jan Kraemer <jan.kraemer@vector.com> - 4.0.54-1
- Override the labels of DataPublisher, DataSubscriber,
  RpcClient, and RpcServer instances through the participant
  configuration, extending the already possible override of the topic /
  function name.
- Changed log messages for controller and participant creation, message
  tracing, system state tracker and time sync service
- Revised the documentation (demos, troubleshooting, doxygen output, file
  structure)
- Improved platform/compiler/architecture detection
- Failure to configure and package cross-builds to QNX on Windows
