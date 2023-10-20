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
You will need the debhelper and debhelper-cmake tools::

    > sudo apt install debhelper devscripts dh-cmake

Getting the source code
========================

You need to recursively clone the source code and the debian helper files from ``git@github1.vg.vector.int:jkraemer/sil-kit-packaging.git``
To actually build the ``.deb`` files, we first need to rename the directory, since the directory needs to follow the scheme ``$PACKAGENAME-$MAJOR.$MINOR.$REVISION``:: 

    > git clone --recursive git@github1.vg.vector.int:jkraemer/sil-kit-packaging.git
    > cd ../
    > mv sil-kit-packaging libsilkit-${MAJOR}.${MINOR}.${REVISION}
    > cd libsilkit-${MAJOR}.${MINOR}.${REVISION}

Alternatively you can also force the naming scheme later on with ``dh_make`` 

Setting up the debian folder
=============================

You can set up the debian folder using the following command. Usually debuild/debhelper need a
tarball with the source code present. Since we run from a ``git`` directory we need to instruct
``dh_make`` to create such an archive, even if we can later ignore it::

    # If you renamed the source directory correctly in the previous step
    > dh_make --createorig
    # If you omitted the renaming
    > dh_make -p $PACKAGENAME_$MAJOR.$MINOR.$REVISION

Please note that the ``-p`` argument uses an underscore ``_`` to separate **$PACKAGENAME_** from **$VERSION_**, while the
renamed directory uses a dash ``-``

Building the .deb file
=======================
To build the ``.deb`` file, we can use the ``debuild`` command::

    > debuild -us -uc

The ``-us`` and ``-uc`` are development flags from ``dpkg-buildpackage``, which ``debuild`` uses under the
hood to build the packages and allow us to build with with

* unsigned sources (-us)
* unsigned code changes (-uc)

The debuild command will now configure, build and install *_SIL Kit_* in a fakeroot environment and
create the ``.deb`` archive from it. The Packages will be found in the parent directory of
libsilkit-$VERSION. They consist of

- libsilkit_$VERSION-1ubuntu4_amd64.deb
   * regular package
- libsilkit_$VERSION-dev-1ubuntu4_amd64.deb
   * headers for libsilkit
- libsilkit-dbgsym_$VERSION-1ubuntu4_amd64.ddeb
   * debug symbols for libsilkit

You can install them regularly with::

    > sudo apt install ./libsilkit_$VERSION-1ubuntu4_amd64.deb ./libsilkit-dev_$VERSION-1ubuntu4_amd64.deb

CAVEATS
========

* Currently the dependencies are pulled from the ``ThirdParty`` directory. This will not fly in Debian
  Land. To get into Debian we need to pull the dependencies from the Debian itself
  * TODO: Rework the CMake files to make the ThirdParty directory optional
* We do not build the ``docs`` yet.
  * Need to put the ``docs`` in a seperate ``docs`` pacakge (CPACK)
  * Need to figure out how to add rules for different packages in the ``rules`` file
* Why are there exe files in my Linux package?
* Need to write systemd unit files to register the ``sil-kit-registry`` as a system daemon

