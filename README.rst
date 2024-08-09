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
To build the libsilkit4 package, you will need the debhelper and debhelper-cmake tools:

* debhelper
* devscripts
* dh-cmake

To build sil-kit itself, you will need the following packages:

* cmake
* ninja-build

Install these packages via::

    > sudo apt install debhelper dpkg-dev devscripts dh-make cmake ninja-build

Setting up the build environment
================================

sil-kit-pkg is setup to work with Github Actions out of the box. But since the main workhorse of the Workflow is the `build_deb.sh` shellscript, which you can find in ``.github/actions/build_deb.sh``, you can also build it locally yourself!
The ``build_deb.sh`` uses environment variables for its setup. These environment variable map to parameters that you can set in the github action.

The following environment variables need to be set

SILKIT_SOURCE_URL: Points to the SIL Kit sources::

    export SILKIT_SOURCE_URL=https://github.com/vectorgrp/sil-kit

SILKIT_PKG_URL: URL to the sil-kit-pkg sources::

    export SILKIT_PKG_URL=/path/to/sil-kit-pkg  # To use a local sil-kit-pkg
    export SILKIT_PKG_URL=https://git.repo.com/your-sil-kit-pkg.git # Use a specific sil-kit-pkg git repo

DEBFULLNAME: Name of the package maintainer/creator::

    export DEBFULLNAME="Awesome Dev"

DEBEMAIL: Email of the package maintainer/creator::

    export DEBEMAIL=awesome_dev@your-domain.something

SILKIT_VENDORED_PACKAGES: Instructs the build script to use the vendored 3rd party libraries

    export SILKIT_VENDORED_PACKAGES

These environment variables also map to Github Actions input parameters.

Additional Parameters for the CI
================================

In addition to the environment variables (used by build_deb.sh), the Github Action uses some more inputs to identify/store the correct artifacts

* debian_arch

    The cpu architecture the debian package is build for. Currently we only support/test on **amd64**

Building the package
====================

Locally
-------

Some further prerequisites:

* We build the package directly in the sil-kit-pkg directory.
    You can copy the script to anywhere on your system, just adapt **SILKIT_PKG_URL** accordingly
* sil-kit-pkg is versioned akine to sil-kit, e.g. sil-kit-pkg version 4.0.44 will ONLY build sil-kit 4.0.44
    This is due to strict (and correct) version handling for Debian packages
    They will always be versioned and the intent is to only built correct versioned packages and it should not be possible to build version 4.0.32 and pretend it is 4.0.44 in the Debian package.
    So if you want to build **sil-kit** version X.Y.Z you need to checkout the vX.Y.Z tag of **sil-kit-pkg**.

Setting up the environment
**************************

.. code-block:: shell
    cd /path/to/sil-kit-pkg
    export SILKIT_SOURCE_URL=https://github.com/vectorgrp/sil-kit.git # The original SIL Kit repo
    export SILKIT_PKG_URL=. # The directory where our **debian** directory lives
    export DEBFULLNAME="awesome.dev@some-mail-provider.com

Building the package
********************
The `build_deb.sh` script can be used to build the SilKit package. It takes the current Ubuntu release version as an optional argument. E.g. to run it on Ubuntu 22.04 use:
.. code-block:: shell
    ./.github/actions/build_deb.sh 22.04

2-5 minutes later a freshly build  will be available in your working directory.
The script should create the following files:

* libsilkit-dev_$VERSION_amd64.deb
* libsilkit4-dbgsym_$VERSION_amd64.ddeb
* libsilkit4_4.$VERSION_amd64.deb
* libsilkit_$VERSION.debian.tar.xz
* libsilkit_$VERSION.dsc
* libsilkit_$VERSION_amd64.build
* libsilkit_$VERSION_amd64.buildinfo
* libsilkit_$VERSION_amd64.changes
* silkit-utils-dbgsym_$VERSION_amd64.ddeb
* silkit-utils_$VERSION_amd64.deb


Github CI
---------

If you have forked sil-kit-pkg and you can use Github Actions, this is how you can build a libsilkit4 package

How to get to the Action
************************

* Click on the ``Actions`` tab in your Github repo
* Click on the ``.github/workflows/package-debian.yml`` tab
* Click on the ``Run Workflow`` tab

Setup for the Workflow
**********************

See `Setting up the environment`_. Additionally set the following variables:

* DEBIAN_ARCH
    amd64

Click the ``Run Workflow`` Button. The `.deb` packages will be in the artifacts of this Workflow run.
