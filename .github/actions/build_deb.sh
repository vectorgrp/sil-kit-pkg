#! /bin/sh

echo "Building the SIL Kit packages"

orig_tarball=${SILKIT_SOURCE_URL}/${SILKIT_VERSION}-${SILKIT_VERSION_SUFFIX}/libsilkit_${SILKIT_VERSION}.orig.tar.xz
wget --no-proxy --no-check-certificate $orig_tarball
ret_val=$?
if [ "$ret_val" != '0' ] ; then
    echo "SILKIT-PKG: Could not get orig tarball from $orig_tarball"
    exit 64
fi

mkdir -p libsilkit-${SILKIT_VERSION}
tar -xvf libsilkit_${SILKIT_VERSION}.orig.tar.xz -C libsilkit-${SILKIT_VERSION}
ret_val=$?
if [ "$ret_val" != '0' ] ; then
    echo "SILKIT-PKG: Could not untar orig tarball $orig_tarball"
    exit 64
fi

git -c http.sslVerify=false clone ${SILKIT_PACKAGING_REPO} -b ${SILKIT_PACKAGING_REPO_BRANCH}
ret_val=$?
if [ "$ret_val" != '0' ] ; then
    echo "SILKIT-PKG: Could not clone $SILKIT_PACKAGING_REPO : $SILKIT_PACKAGING_REPO_BRANCH"
    exit 64
fi

SILKIT_PACKAGE_REPO_NAME=$(echo ${SILKIT_PACKAGING_REPO} | awk -F/ '{print $NF}' | awk -F. '{print $1}')
echo "PACKAGING REPO NAME ${SILKIT_PACKAGE_REPO_NAME}"
mv ./${SILKIT_PACKAGE_REPO_NAME}/debian libsilkit-${SILKIT_VERSION}

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

#echo "Copying artifacts"
#SILKIT_VERSION_MAJOR=$(echo ${SILKIT_VERSION} | cut -d '.' -f1)
