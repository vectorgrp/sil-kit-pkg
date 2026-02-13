%define version_major 5
%define version_minor 0
%define version_patch 3
%define version_suffix %{nil}



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

* Thu Feb 12 2026 Daniel Edwards <daniel.edwards@vector.com> - 5.0.3
- `sil-kit-registry`: fixed crash whith enabled dashboard
- `sil-kit-registry`: allow configuration of the listen URI, when used as
  Windows system service
- `cmake`: demo and utility `RPATH`s are now set to match the install
  hierarchy on all systems
- `cmake`: use `CMAKE_POLICY_VERSION_MINIMUM` since `oatpp` uses an outdated
  `cmake` version
- `sil-kit-registry`: stop force-disabling the dashboard when building Linux
  packages
- `docs`: added description of handling of CAN message sizes
- `cmake`: added explicit build options to QNX presets
- `flexray`: add second keyslot parameters to the FlexRay node parameters

* Thu Dec 04 2025 Jan Kraemer <jan.kraemer@vector.com> - 5.0.2
- `asio`: replaced the deprecated (and now removed) methods
  `asio::io_context::post` and `asio::io_context::dispatch` with the
  suggested alternatives `asio::post` and `asio::dispatch`
- `capi`: fixed an include cycle between `silkit/capi/EventProducer.h` and
  `silkit/capi/NetworkSimulator.h`
- `sil-kit-monitor`: fixed missing output due to changes to the default
  loglevels
- `logs`: fixed logging in JSON format without any key-value pairs
- `docs`: fixed broken formatting in `troubleshooting/advanced`
- `ci`: fixed usage of cmake for macOS runners
- `cmake`: fixed QNX preset and toolset
- `git`: fixed broken build dir glob pattern in `.gitignore` file
- `quality`: fixed various warnings# Changed
- `sil-kit-system-controller`: improved the behavior of the `sil-kit-system-
  controller`, allowing single participants to drop out and rejoin before
  all required participants are connected without having to restart other
  required participants or the system controller.
- `docs`: document the ability to override the history length of
  `DataPublisher` controllers in the participant configuration
- `sil-kit-registry`: enable collecting metrics by default
- `tests`: added timeout for the participant modes test and a separate
  (overall) timeout for test execution in the CI
- `cmake`: added the `distrib` preset and removed various superfluous presets
- `docs`: document the (experimental) configuration settings that influence
  metrics generation and collection
- `quality`: made multiple derived classes `final`# Added
- `sil-kit-monitor`: add `-l` / `--loglevel` commandline arguments to control
  the log level
- `logs`: added message target in the `To` key-value field of trace messages
- `logs`: add trace logs for sending a historized pub/sub messages
- `logs`: added a `raw` key for arbitrary JSON objects in log messages
- `ci`: added `clang-tidy` to the CI
- `ci`: added devcontainer for `clang-format`, format all files, and ensure
  that the check is enabled in the CI
- `ci`: added a check to ensure that all commits are properly `Signed-of-by`
  as defined by [DCO](https://wiki.linuxfoundation.org/dco)

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
