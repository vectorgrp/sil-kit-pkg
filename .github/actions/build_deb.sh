#! /bin/sh

echo "Building the SIL Kit packages"

if [ -z $SILKIT_PKG_URL ] ; then
    SILKIT_PKG_URL="."
fi
debian_path="${SILKIT_PKG_URL}/debian"

silkit_pkg_found=false
# Check if the provided path has a debian directory
if [ ! -d ${debian_path} ] ; then
    echo "SILKIT-PKG: Could not find local debian directory, trying to clone the sil-kit-pkg git repo!"
    git -c http.sslVerify=false clone --depth=1 ${SILKIT_PKG_URL} -b ${SILKIT_PKG_REF} sil-kit-pkg
    ret_val=$?
    if [ "$ret_val" != '0' ] ; then
        echo "SILKIT-PKG: Could not clone $SILKIT_PKG_URL : $SILKIT_PKG_REF"
        exit 64
    fi
    debian_path="./sil-kit-pkg/debian"
fi


SILKIT_FULL_VERSION=`sed -En "s/libsilkit \(([0-9]+\.[0-9]+\.[0-9]+)-*([0-9]+).*/\1 \2/p" $debian_path/changelog`
SILKIT_VERSION=`echo $SILKIT_FULL_VERSION | cut -d ' ' -f1`
SILKIT_DEBIAN_REVISION=`echo $SILKIT_FULL_VERSION | cut -d ' ' -f2`
echo "Packaging SILKIT Version $SILKIT_VERSION"
echo "Packaging DEBIAN Version $SILKIT_DEBIAN_REVISION"

# Check if running in CI
if [ -n "${CI_RUN+1}" ] ; then

    echo "Saving VERSION and REVISION to Github step outputs!"
    echo "silkit_version=${SILKIT_VERSION}" >> "$GITHUB_OUTPUT"
    echo "silkit_debian_revision=${SILKIT_DEBIAN_REVISION}" >> "$GITHUB_OUTPUT"
fi

if [ -n SILKIT_VENDORED_PACKAGES ] ; then
   SUBMODULE_CMD="--recurse-submodules --shallow-submodules"
else
   SUBMODULE_CMD=""
fi


if [ -n SILKIT_REVISION ] ; then
    CLONE_VERSION="main"
else
    CLONE_VERSION="sil-kit/v${SILKIT_VERSION}"
fi

git -c http.sslVerify=false clone ${SUBMODULE_CMD} --depth=1 ${SILKIT_SOURCE_URL} -b ${CLONE_VERSION} libsilkit-${SILKIT_VERSION}
ret_val=$?
if [ "$ret_val" != '0' ] ; then
    echo "SILKIT-PKG: Could get SIL Kit sources at ${SILKIT_SOURCE_URL}:${SILKIT_REVISION}"
    echo "Trying local directory at ${PWD}/libsilkit-${SILKIT_VERSION}"
fi

if [ ! -d ./libsilkit-${SILKIT_VERSION} ]; then
    echo "No SIL Kit sources found!"
    exit 64
fi

echo "SILKIT REVISION: ${SILKIT_REVISION}"
echo
if [ -n $SILKIT_REVISION ] ; then
    git -C ./libsilkit-${SILKIT_VERSION} reset --hard ${SILKIT_REVISION}
fi

tar --exclude='.git' -cJf libsilkit_${SILKIT_VERSION}.orig.tar.xz -C libsilkit-${SILKIT_VERSION} .
ret_val=$?
if [ "$ret_val" != '0' ] ; then
    echo "SILKIT-PKG: Could create orig tarball $orig_tarball"
    exit 64
fi

cp -r ${debian_path} libsilkit-${SILKIT_VERSION}
cd libsilkit-${SILKIT_VERSION}/

echo "Running dh_make"
dh_make -ly
ret_val=$?
if [ "$ret_val" -gt '1' ] ; then
    echo "SILKIT-PKG: \"dh_make -ly\" exit code $ret_val"
    exit 64
fi

echo "Running debuild"
debuild -us -uc --lintian-opts -E --pedantic
ret_val=$?
if [ "$ret_val" != '0' ] ; then
    echo "SILKIT-PKG: \"debuild -us -uc\" exit code $ret_val"
    exit 64
fi
