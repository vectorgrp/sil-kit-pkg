%define version_major 5
%define version_minor 0
%define version_patch 8
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

* Tue Oct 13 2026 Konrad Breitsprecher <konrad.breitsprecher@vector.com> - 5.0.8
- The 5.0.8 (or later) MSI can't detect or remove an earlier per-user
  installation, so both will be on the system side by side.
- Upgrading still works. The new installer: - removes the previous
  `VectorSilKitRegistry` service and installs the `SilKitRegistry` system
  service of the new version, - sets the `SilKit_InstallDir` environment
  variable to the new installation, and - updates the CMake `find_package`
  lookup to find the new installation.
- Uninstalling the old version is **optional** and only cleans up. To do it,
  open *Settings > Apps > Installed apps* (or *Programs and Features*) **as
  the user who originally installed it** and uninstall the old SIL Kit
  entry.## "Vector" branding removed | Up to 5.0.7 | From 5.0.8
  |---|---|---| Installation folder | `<ProgramFiles>\Vector SIL Kit
  <VERSION>` | `<ProgramFiles>\SIL Kit <VERSION>` | Registry system service
  | `VectorSilKitRegistry` | `SilKitRegistry` | Service config file |
  `<ProgramData>\Vector SIL Kit\silkit-registry.yaml` | `<ProgramData>\SIL
  Kit\silkit-registry.yaml` |he old `<ProgramData>\Vector SIL Kit` folder is
  not removed. If you customized `silkit-registry.yaml`, copy it to the new
  location.# Added
- Add Integration Test for Timestamp Behavior
- Add Integration Test for Remote Logging
- The documentation now explains the delineation between fast (trivial) and
  accurate (detailed, network simulator based) simulation, including notes
  for LIN.
- The documentation now lists every third party dependency found in the source
  tree with its version and license on the Licenses page, followed by the
  full license text of each component that ships one.# Fixed
- The SIL Kit Registry could hang on shutdown when a configured dashboard
  server accepted the connection but never answered. Dashboard requests now
  have connect, write and read deadlines, and an in-flight request is
  aborted after a grace period so that shutdown is always bounded.
- A malformed or unexpected response from the dashboard service no longer
  terminates the registry's dashboard worker thread; unknown fields in the
  response are now ignored.
- The SIL Kit Registry could call into a destroyed dashboard instance while
  still serving traffic, because the dashboard was torn down before the
  registry that holds a pointer to it.
- If the dashboard service did not support the bulk-update endpoint, the
  registry's dashboard worker thread stopped while events kept accumulating
  in an unbounded queue. The capability probe has been removed; the worker
  now keeps draining the queue and reports the failing requests instead.
  This also removes one request during registry startup.
- Dashboard events accumulated but not yet sent are now flushed when the
  registry shuts down, instead of being discarded.
- Log messages from the dashboard instance and its worker thread carry the
  `Dashboard` log topic again; they were previously emitted without a topic
  and so escaped topic filtering.
- Fix ITest_AsyncSimTask (test failed when run repeatedly)
- Fix the `TimeSyncService` warning about an exceeded soft time limit, which
  showed a literal `{}` instead of the measured timeout in milliseconds
- The third party license notices were incomplete. They now also cover
  components that are vendored inside another dependency, such as c4core
  inside the rapidyaml sources, and the components that ship inside the HTML
  documentation. `ThirdParty/LICENSES.rst` is generated from a software bill
  of materials and is the file the documentation shows, so the two can no
  longer disagree.
- The SIL Kit Registry silently listened on local domain sockets only when its
  listen URI contained an invalid or unresolvable host. It now fails to
  start with a configuration error naming the host.
- The SIL Kit Registry did not listen over TCP on bracketed IPv6 addresses,
  e.g., `silkit://[::1]:8500`, on platforms whose address parser rejects the
  brackets.
- Bracketed IPv6 addresses containing hexadecimal digits, e.g.,
  `tcp://[2001:db8::1]:8500`, were passed to the system resolver, which
  rejects them. A participant configured to accept connections on such an
  address failed to join, and a peer advertising one was not connected to on
  it.
- `ISilKitRegistry::GetLogger()` returned `nullptr`, and the C API
  `SilKit_Vendor_Vector_SilKitRegistry_GetLogger` returned a pointer of the
  wrong internal type. Both now return the registry's logger.
- A participant in the `Running` or `Paused` state could miss the system-wide
  stop if its locally computed system state went directly to `Stopped`
  without passing `Stopping`. The participant now also stops in that case.
- The PCAP trace sink did not actually take its lock when tracing Ethernet
  frames, and opening and closing the sink were unsynchronized, allowing a
  data race.
- PCAP trace files had wrong packet timestamps. Their header announces
  nanosecond resolution, but the packet timestamps were written in
  microseconds. Packet timestamps are now written in nanoseconds.# Changed
- `third-party`: the dashboard client no longer depends on `oatpp`, and the
  `ThirdParty/oatpp` submodule has been removed. The dashboard payloads are
  now built with the already-bundled `rapidyaml`, and the REST requests are
  issued over the already-bundled standalone `asio`. The requests the
  dashboard service receives are unchanged apart from three cosmetic
  differences in the JSON encoding: a space follows each `:` separator,
  forward slashes are no longer escaped as `\/`, and non-ASCII characters
  are sent as UTF-8 rather than `\uXXXX` escapes. Control characters that
  cannot be escaped are replaced with U+FFFD.
- `third-party`: the SIL Kit build now defines `ASIO_NO_DEPRECATED`, so that
  using an asio interface that upstream has deprecated is a build error
  rather than something that only surfaces when asio removes it. No SIL Kit
  source used one.
- Running a build without dashboard support (`SILKIT_BUILD_DASHBOARD=OFF`) and
  passing `--dashboard-uri` now reports plainly that this build has no
  dashboard support, instead of printing an error about a failed dashboard
  instance creation.
- A `--dashboard-uri` whose scheme is not `http` is now rejected when the
  dashboard instance is created. The dashboard client only ever spoke
  plaintext HTTP, so an `https://` URI was previously accepted and silently
  downgraded.
- Changes to the SIL KIT MSI installer: - Default installation path changed
  from `<ProgramFilesFolder>\Vector SIL Kit <VERSION>` to
  `<ProgramFilesFolder>\SIL Kit <VERSION>` - Windows System Service Name
  changed from `VectorSilKitRegistry` to `SilKitRegistry` - SIL Kit Registry
  System Service config file installation path changed from
  `<ProgramDataFolder>\Vector SIL Kit\silkit-registry.yaml` to
  `<ProgramDataFolder>\SIL Kit\silkit-registry.yaml` - Note that the
  `<ProgramDataFolder>\Vector SIL Kit` is not removed by installing
  `SilKit-5.0.8.msi`.
- PCAP replay now also reads PCAP files with microsecond resolution, e.g., as
  written by tcpdump or Wireshark. Previously only nanosecond resolution
  files were accepted.
- `TimeSyncService` now throws `LogicError{"TimeSyncPolicy is not set"}` if
  `CompleteSimulationStep` is used before `StartLifecyle`.

* Wed Jul 29 2026 Konrad Breitsprecher <konrad.breitsprecher@vector.com> - 5.0.7
- `config`: experimental topic based filtering of log messages per logging
  sink via `Experimental/EnabledTopics` and `Experimental/DisabledTopics`.
  Log messages are tagged with a topic that classifies their origin (e.g.,
  `Asio`, `Ethernet`, `Participant`, `User`).
- `docs`: added description of the experimental logging topics, including the
  list of topic names currently assigned by SIL Kit components.# Fixed
- `core`: on peer shutdown, the disconnected peer is removed from the pending
  subscription acknowledges. Otherwise, participants could wait indefinitely
  for acknowledges that will never arrive.
- `config`: the participant configuration is now validated against the schema.
  Previously, only included configuration files were validated, the root
  configuration was not.
- `config`: added missing entries to the participant configuration JSON schema
  and the schema validation (e.g., `Experimental/Metrics/UpdateInterval`,
  `RpcClients/RpcChannel`, `RpcServers/RpcChannel`).
- `api`: the public header `silkit/services/logging/string_utils.hpp` no
  longer includes internal headers.
- `config`: experimental
  `Experimental.TimeSynchronization.DynamicSimulationStep` to enable dynamic
  simulation step sizes, aligning each simulation step to the minimal step
  among all synchronized participants. Tri-state: `true` requests it for the
  whole simulation, `false` opts out, and leaving it unset follows the
  network. Off by default.# Changed
- `config`: default format of file logging is set to JSON. Set "Format:
  Simple" in the sink to get previous behaviour.
- `docs`: added description of the logging "Format".
- `docs`: added deprecation warning for Ubuntu 20.04
- `build`: the CMake targets only expose the top-level include directory
  instead of internal include directories.# Fixed
- `config`: a mapping that is mistyped as a YAML sequence (e.g. a stray
  leading `- ` turning `HealthCheck` into a list) is now rejected with a
  clear error instead of being silently accepted.
- `config`: a configuration containing multiple `---`-separated YAML documents
  is now rejected with a clear error. A single leading `---` remains valid.
- `orchestration`: setting a simulation step duration of zero now raises a
  `SilKitError` instead of being silently accepted.
- `logging`: Fixes a bug where some log messages (e.g., user-level log
  messages) were passed to fmt and caused exceptions when placeholder
  characters were present. These log messages are no longer passed to
  fmt.

* Thu Jun 11 2026 Konrad Breitsprecher <konrad.breitsprecher@vector.com> - 5.0.6
- `demo`: removed third-party dependency from performance test script
- `docs`: Fixed ethernet docs and samples
- `build`: Silence warning emitted from oatpp
- `ci`: Fix version check and tooling in ci formatting check
- `build`: Update deprecated syntax in devcontainter

* Thu May 21 2026 Lukas Becker <lukas.becker@vector.com> - 5.0.5
- `lin`: fixed missing reception of the Go-To-Sleep frame by the master after
  `GoToSleep()` in detailed simulation# Changed
- `cmake`: merged almost all internal CMake `INTERFACE` libraries into
  `I_SilKit`
- `third-party`: update `oatpp` to version 1.3.1
- `docs`: update the supported platforms table
- `docs`: Extend docs by available metrics
- `docs`: Add missing related products
- `quality`: following small improvements - add missing `#pragma once` - add
  `static` to some TU-local functions - add `inline` to some header-defined
  functions - remove an obsolete source file - adjust warning flags

* Fri Mar 27 2026 Daniel Edwards <daniel.edwards@vector.com> - 5.0.4
- `docs`: removed 'Vector' prefix where SIL Kit is mentioned in multiple
  places
- `demos`: improved code quality# Fixed
- `pubsub` / `rpc`: fix some edge cases when matching labels
- `lin`: fixed TX/RX behavior when controller is not operational
- `lin`: populate the `timestamp` field in `LinControllerStatusUpdate` message

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
