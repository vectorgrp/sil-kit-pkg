#! /bin/sh

echo "Building the SIL Kit packages"

wget --no-proxy --no-check-certificate ${SILKIT_SOURCE_URL}/${SILKIT_VERSION}-${SILKIT_VERSION_SUFFIX}/libsilkit_${SILKIT_VERSION}.orig.tar.xz

mkdir libsilkit-${SILKIT_VERSION}
tar -xvf libsilkit_${SILKIT_VERSION}.orig.tar.xz -C libsilkit-${SILKIT_VERSION}

git -c http.sslVerify=false clone ${SILKIT_PACKAGING_REPO}

SILKIT_PACKAGE_REPO_NAME=$(echo ${SILKIT_PACKAGING_REPO} | awk -F/ '{print $NF}' | awk -F. '{print $1}')
echo "PACKAGING REPO NAME ${SILKIT_PACKAGE_REPO_NAME}"
mv ./${SILKIT_PACKAGE_REPO_NAME}/debian libsilkit-${SILKIT_VERSION}

cd libsilkit-${SILKIT_VERSION}/

echo "Running dh_make"
dh_make -ly
echo "Running debuild"
debuild -us -uc

echo "Copying artifacts"
SILKIT_VERSION_MAJOR=$(echo ${SILKIT_VERSION} | cut -d '.' -f1)

