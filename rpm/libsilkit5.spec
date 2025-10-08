%define version_major 5
%define version_minor 0
%define version_patch 2
%define version_suffix rc1


%if "%{version_suffix}" == ""
%define silkit_version %{version_major}.%{version_minor}.%{version_patch}
%else
%define silkit_version %{version_major}.%{version_minor}.%{version_patch}~%{version_suffix}
%endif

Name:       libsilkit5
Version:    %{silkit_version}
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
Obsoletes: libsilkit4
Conflicts: libsilkit4

%description
An open-source library for connecting Software-in-the-Loop Environments

%package devel
Summary: Develop Files for the libsilkit package
Requires: libsilkit%{version_major}

%description devel
The development headers and CMake files for libsilkit

%package utils
Summary: SilKit Util Binaries
Requires: libsilkit%{version_major}

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
        -DSILKIT_BUILD_DEMOS=Off \\\
        -S . \\\
        -GNinja \\\
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \\\
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
%{_libdir}/libSilKit.so.%{version_major}*

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

* Wed Oct 08 2025 asd <asd> - 5.0.2
- `asio`: replaced the deprecated (and now removed) methods
  `asio::io_context::post` and `asio::io_context::dispatch`

* Wed Sep 24 2025 Jan Kraemer <jan.kraemer@vector.com> - 5.0.2~rc1
- New Pre-Release

* Wed Aug 06 2025 Jan Kraemer <jan.kraemer@vector.com> - 5.0.1
- Fix building SIL Kit from source

* Thu Jul 17 2025 Jan Kraemer <jan.kraemer@vector.com> - 5.0.0
- API: added new SilKit_ParticipantConfiguration_ToJson function which exports
  the complete parsed and validated participant configuration as a JSON string.
- dashboard: add performance related metrics.
- public API: removed harmful noexcept and added a missing virtual destructor.
- dashboard: removed legacy v1.0 API.
- build: the internal code now uses C++17
- config: we replaced yaml-cpp with rapidyaml and rewrote the YAML/JSON parsing.

* Mon May 19 2025 Jan Kraemer <jan.kraemer@vector.com> - 4.0.56-1
- Three static methods which are part of the C++ (Hourglass) API
  implementation and passed as callbacks to the C-API, did not use the
  correct calling convention if the default calling convention wasn't
  __cdecl on Windows. This has been remedied.
- SilKitDemoSimStepAsync did not work as intended, due to the predicate
  lambda capturing by-value instead of by-reference
- The participant configuration TcpNoDelay now defaults to true. Please
  note, that this has performance implications. On Linux platforms this
  improves throughput, and latency in particular when used in combination
  with TcpQuickAck: true
- The documentation now contains a page that explains the upcoming new
  versioning scheme. Experimental other-simulation-steps-completed API

* Fri Feb 07 2025 Jan Kraemer <jan.kraemer@vector.com> - 4.0.56~rc1
- New pre release
* Wed Jan 29 2025 Jan Kraemer <jan.kraemer@vector.com> - 4.0.55-1
- SilKit_LinDataLengthUnknown in the C header Lin.h has been turned into
  a define like all the other constants in the C header files.
- Aligned C API error return codes SilKit_ReturnCode_XXX and SIL Kit
  specific exceptions.
- Demos: Overhauled and restructured most existing demos.
- Demos: Added SimpleCan and Orchestration demos for basic API usage.
- Demos: Added sample participant configuration files.
- Registry: Block all attempts to connect with an already present
  participant name, not just the first.
- CMake: When demos are installed into the bin directory under the
  installation prefix, their RPATH will be set such that they are able to
  find the libSilKit[d].so.
- System Monitor: Show all participants, not just the ones that joined
  during the monitors execution.
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
