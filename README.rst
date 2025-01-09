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
    * Determines the package type to build. ``deb`` for Debian/Ubuntu builds. ``rpm`` for RedHat/Fedora builds.
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

Additional Parameters for the CI
================================

In addition to the environment variables (used by build_deb.sh), the Github Action uses some more inputs to identify/store the correct artifacts

* debian_arch

    The cpu architecture the debian package is build for. Currently we only support/test on **amd64**

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

If you have forked sil-kit-pkg and you can use Github Actions, this is how you can build a libsilkit4 package

How to get to the Action
************************

* Click on the ``Actions`` tab in your Github repo
* Click on the ``Silkit Packaging Workflow`` tab
* Click on the ``Run Workflow`` tab

Setup for the Workflow
**********************

* SIL Kit Repository URL
  Set to the sil-kit github repo
* SIL Kit Source Repo ref
  Set to the branch/tag/commit id of the sil-kit repo you want to use
* sil-kit-pkg ref
  If you want to build a release you can set the this to a release tag
* Maintainer name (only used on Debian/Ubuntu)
  Name of the maintainer creating the package
* Maintainer email (only used on Debian/Ubuntu)
  Email of the maintainer creating the package

* DEBIAN_ARCH
    amd64

Click the ``Run Workflow`` Button. Packages for Ubuntu 20.04 and Alma Linux 9 will be in the artifacts of this Workflow run.
