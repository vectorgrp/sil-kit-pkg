#! /bin/sh

echo "Building the SIL Kit packages"

if [ -z $SILKIT_PKG_URL ] ; then
    SILKIT_PKG_URL="."
fi
debian_path="${SILKIT_PKG_URL}/debian"

silkit_pkg_found=false
# Check if the provided path has a debian directory
if [ -d ${debian_path} ] ; then
    silkit_pkg_found=true
fi

if ! $silkit_pkg_found ; then
    echo "SILKIT-PKG: Trying git sil-kit-pkg"
    if git ls-remote -hq ${SILKIT_PKG_URL} ; then
        git -c http.sslVerify=false clone --depth=1 ${SILKIT_PKG_URL} -b ${SILKIT_PKG_REF} sil-kit-pkg
        ret_val=$?
        if [ "$ret_val" != '0' ] ; then
            echo "SILKIT-PKG: Could not clone $SILKIT_PKG_URL : $SILKIT_PKG_REF"
            exit 64
        fi
        debian_path="./sil-kit-pkg/debian"
    fi
fi


SILKIT_FULL_VERSION=`sed -En "s/libsilkit \(([0-9]+\.[0-9]+\.[0-9]+)-*([0-9]+).*/\1 \2/p" $debian_path/changelog`
SILKIT_VERSION=`echo $SILKIT_FULL_VERSION | cut -d ' ' -f1`
SILKIT_DEBIAN_REVISION=`echo $SILKIT_FULL_VERSION | cut -d ' ' -f2`
echo "Packaging SILKIT Version $SILKIT_VERSION"
echo "Packaging DEBIAN Version $SILKIT_DEBIAN_REVISION"

# Check if running in CI
if [ -n ${CI_RUN+1} ] ; then

    echo "Saving VERSION and REVISION to Github step outputs!"
    echo "silkit_version=${SILKIT_VERSION}" >> "$GITHUB_OUTPUT"
    echo "silkit_debian_revision=${SILKIT_DEBIAN_REVISION}" >> "$GITHUB_OUTPUT"
fi

if git ls-remote -hq ${SILKIT_SOURCE_URL} ; then
    git -c http.sslVerify=false clone ${SILKIT_SOURCE_URL} --depth=1 -b "sil-kit/v${SILKIT_VERSION}" libsilkit-${SILKIT_VERSION}
    ret_val=$?
    if [ "$ret_val" != '0' ] ; then
        echo "SILKIT-PKG: Could get SIL Kit sources at ${SILKIT_SOURCE_URL}:silkit/v${SILKIT_VERSION}"
        exit 64
    fi
    tar -cJf libsilkit_${SILKIT_VERSION}.orig.tar.xz -C libsilkit-${SILKIT_VERSION} .
    ret_val=$?
    if [ "$ret_val" != '0' ] ; then
        echo "SILKIT-PKG: Could create orig tarball $orig_tarball"
        exit 64
    fi
    orig_found=true
fi

if ! $orig_found ; then
    echo "SILKIT-PKG: Could not get the SIL Kit sources! Exiting!"
    exit 128
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
debuild -us -uc
ret_val=$?
if [ "$ret_val" != '0' ] ; then
    echo "SILKIT-PKG: \"debuild -us -uc\" exit code $ret_val"
    exit 64
fi
