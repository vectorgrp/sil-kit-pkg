**********************************
The Vector SIL Kit Packaging REPO
**********************************

Prerequisites
==============

Terminology
----------------
If during the course of this README you stumble upon ``$VERSION``, this is a short placeholder for the
typical **SEMVER** ``$MAJOR.$MINOR.$REVISION`` placeholder. Placeholderception if you will!

Packages
---------
To build the libsilkit4 package, the following package related tools are needed:

Ubuntu:

* debhelper
* devscripts
* dh-cmake
* python 3

Fedora:

* fedora-packager tools (installs rpm-build, fedpkg, mock and more tools)
* fedora-review

To build sil-kit itself, you will need the following packages:

* cmake
* ninja-build
* clang/llvm

Install these packages via::

    # Debian/Ubuntu
    > sudo apt install debhelper dpkg-dev devscripts dh-make cmake ninja-build clang python3
    # Fedora/RHEL
    > sudo dnf install fedora-packager fedora-review cmake ninja-build clang python3

Currently we support building the packages on the following platforms:

* Ubuntu
    * 20.04
    * 22.04
    * 24.04
* Fedora
    * 40+

In addition, relocatable binary tarballs (``pkgformat: tgz``) are built for:

* Ubuntu 20.04 (``ubuntu2004``)
* CentOS 7 (``el7``)
* AlmaLinux 8 (``el8``)

``el7``/``el8``/``el9`` stand for Enterprise Linux 7/8/9, i.e. RHEL and its binary compatible
rebuilds (CentOS 7 = el7, AlmaLinux 8 = el8, AlmaLinux 9 = el9).

Release definition
==================

``release/packages.json`` is the single source of truth for the Linux packages. Every entry
(target) names the build image, the package format and platform, the plain distribution image
used for the smoke test, whether it is released (``release``) and the files that make up the
package (``assets``, glob patterns).

The packaging workflow builds every target. sil-kit-delivery publishes the assets of all targets
with ``"release": true`` to the GitHub releases of ``vectorgrp/sil-kit`` and ``vectorgrp/sil-kit-pkg``.

Containers
==========

The build images live in ``containers/`` and are published to
``ghcr.io/vectorgrp/sil-kit-pkg/<name>`` by the ``Build Images`` workflow
(``.github/workflows/build-images.yml``) on every change on ``main``:

* ``ubuntu-2004``: deb and tarball for Ubuntu 20.04
* ``ubuntu-2204``: arm64 deb (built on an arm64 runner)
* ``centos-7``: el7 tarball, devtoolset-11
* ``alma-8``: el8 tarball, gcc-toolset-12
* ``fedora-40``: el9 rpm via mock

Only public sources are used: base images are pinned by digest, CMake comes from the official
Kitware release and ninja from the official PyPI wheel, both verified by sha256. Once the images
are published, pin them by digest in ``release/packages.json``
(``ghcr.io/vectorgrp/sil-kit-pkg/<name>@sha256:...``, the digest is in the job summary of the
``Build Images`` run).

Tarballs
========

``libsilkit-$VERSION.<platform>.x86_64.tar.gz`` contains ``bin/``, ``lib/`` (with the CMake
package config in ``lib/cmake/SilKit``), ``include/``, ``share/man/man1/``,
``share/sil-kit/sil-kit-registry.service`` and ``share/doc/libsilkit/`` (``CHANGELOG.md``,
``LICENSE``, ``README.rst``). It can be extracted anywhere::

    tar -xzf libsilkit-$VERSION.el7.x86_64.tar.gz
    cmake -DCMAKE_PREFIX_PATH=$PWD/libsilkit-$VERSION.el7.x86_64 ...

The debug symbols are in ``libsilkit-$VERSION.<platform>.x86_64.debug.tar.gz`` under
``lib/debug/.build-id/``. Point gdb at them with ``set debug-file-directory <extracted>/lib/debug``.

The tarballs are reproducible: the same sil-kit commit, sil-kit-pkg commit and image give
identical files (``SOURCE_DATE_EPOCH`` is the commit time of the sil-kit sources). The
``Rebuild Check`` workflow verifies this by building everything twice.

Setting up the build environment
================================

sil-kit-pkg is setup to work with Github Actions out of the box. But since the main workhorse of the Workflow is the ``silkit_linux_packaging.py`` shellscript, which you can find in ``scripts/silkit_linux_packaging.py``, you can also build it locally yourself!

The Config
----------
The ``silkit_linux_packaging.py`` script uses a JSON config for its setup. These config options map to parameters that you can set in the github action.

Let's examine an example config to build a SIL Kit package: ::

    {

        "SilKitInfo": {
              "url": "https://github.com/vectorgrp/sil-kit.git",
              "ref": "v4.0.54",
              "recursive": true,
              "is_local": false
        },
        "package_repo_path": "sil-kit-pkg",
        "version": {
              "major": 4,
              "minor": 0,
              "patch": 54,
              "suffix": ""
        },
        "pkgformat": "deb",
        "work_dir": "./workdir",
        "keep_temp": true,
        "output_dir": "./out",
        "platform": "Ubuntu-22.04"
    }



* SilKitInfo
    * General information about the silkit sources

* url
    * The url to get the SIL Kit sources. can be a git URL or a local path. In our case we are fetching the sources directly from the upstream Github repo.

* ref
    * The git ref to be fetched, can be a branch or a tag or an actual commit id. In our case we are fetching the tag for version 4.0.54
    * only when using a git url

* recursive
    * Does a recursive clone with all submodules included
    * Only when using a git url

* is_local
    * Set to true when using a local path in the url field

* package_repo_path
    * The path to this (sil-kit-pkg) repo. Can be an absolute path or a path relative to from where you execute the ``silkit_linux_packaging.py`` script.

* version
    * The version of the SIL Kit package to be build
* major
    * The major version of the package
* minor
    * The minor version of the package
* patch
    * The patch version of the package
* suffix
    * Additional version suffix of the package

* pkgformat
    * Determines the package type to build. ``deb`` for Debian/Ubuntu builds. ``rpm`` for RedHat/Fedora builds. ``tgz`` for the relocatable tarballs.
* work_dir
    * The directory where the build is happening
* keep_temp
    * Keeps the working dir after finishing the build. Useful to debug build errors.
* outpur_dir
    * The directory where the (local) artifacts are copied to.
* platform
    * The platform to build for
    * Possible values are
        * Ubuntu-20.04
        * Ubuntu-22.04
        * Ubuntu-24.04
        * epel8
        * epel9
        * fc40
        * ubuntu2004, el7, el8 (``tgz``)

Fedora Extra Packages for Enterprise Linux
-------------------------------------------
When build for the EPEL (Extra Packages for Enterprise Linux) Repos, you need to create a symlink to the correct ``mock`` config, since ``epel-x`` is not the name of a valid config. The official SIL Kit RPM packages are built for ALMA Linux 9, so we can use the ALMA 9 config like this:

.. code-block:: shell

    mkdir -p ~/.config/mock
    ln -sf /etc/mock/alma+epel-9-x86_64.cfg ~/.config/mock/epel-9-x86_64.cfg

Mock will automatically look in the ``~/.config/mock/`` dir for a valid config with the platform name we provide. Creating a symlink with that name to the existing ALMA 9 config will provide this.

Additionally, you need to add your user to the ``mock`` group:

.. code-block:: shell

    # If the group does not already exist
    sudo groupadd mock
    # Adding your $USER
    sudo usermod -aG mock $USER

DEBIAN environment variables
----------------------------

Debian requires the Maintainer environment variables to be set correctly:

.. code-block:: shell

    export DEBFULLNAME="Awesome Dev"
    export DEBEMAIL="awesome_dev@your-domain.something"

Building the package
====================

Locally
-------

Setting up the environment
**************************

Create the JSON config file according to `The Config`_.
If you build the package under Debian/Ubuntu, set the appropriate environment variables.

Building the package
********************
Let's go through an exemplary build using the ``silkit_linux_packaging.py`` script. You can use the `The Config`_ config as a starter template.
We assume that you have checked out the ``sil-kit-pkg`` repo at ``~/workspace/sil-kit-pkg``. Choose ``~/workspace/workdir`` as the ``work_dir`` value and ``~/workspace/out`` as the ``output_dir``.
If you build for Fedora, change the ``pkgformat`` to ``rpm`` and choose the platform according to your current Fedora release e.g. ``f40`` for Fedora 40. You can get a list of all availbale platforms via ``fedpkg releases-info``. Don't forget to symlink the correct config if you are building an ``epel`` package.

The rest of the config can use the template values. Then all you need to run is:

.. code-block:: shell

    python3 sil-kit-pkg/scripts/silkit_linux_packaging.py --build-cfg ./my_config.json

2-5 minutes later a freshl build will be available in your designated output directory.

Github CI
---------

The ``SilKit Packaging Workflow`` (``.github/workflows/package-silkit.yml``) builds all targets of
``release/packages.json``, tests every package in the plain ``test_image`` of its target and
uploads the result as the artifact ``sil-kit-pkg`` (kept for 30 days): all assets,
``pkg-manifest.json`` (sil-kit commit and submodules, sil-kit-pkg commit, image digests,
sha256 and size of every file) and ``SHA256``.

sil-kit-delivery starts it for every delivery build. To run it manually:

* Click on the ``Actions`` tab, then ``SilKit Packaging Workflow``, then ``Run workflow``
* Choose the sil-kit-pkg branch or tag to build from
* ``silkit_ref``: the sil-kit commit SHA or tag, e.g. ``v5.0.8``
* optional: ``expected_version`` fails the run if ``debian/changelog``, ``rpm/libsilkit5.spec``
  and the sil-kit sources do not all have this version
* optional: maintainer name and email for the Debian build (default: ``Maintainer`` in ``debian/control``)

GitHub releases are created by sil-kit-delivery from this artifact, not by this repository.
