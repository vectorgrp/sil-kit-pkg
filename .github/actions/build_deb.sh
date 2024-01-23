#! /bin/sh

echo "Building the SIL Kit packages"

#Check whether SILKIT SOURCE is local
orig_found=false
if [ -f ${SILKIT_SOURCE_URL}/libsilkit_${SILKIT_VERSION}.orig.tar.xz ] ; then
    echo "Found orig tarball at ${SILKIT_SOURCE_URL}/libsilkit_${SILKIT_VERSION}.orig.tar.xz"
    orig_tarball=${SILKIT_SOURCE_URL}/libsilkit_${SILKIT_VERSION}.orig.tar.xz
    cp $orig_tarball ./
    mkdir -p libsilkit-${SILKIT_VERSION}
    tar -xvf libsilkit_${SILKIT_VERSION}.orig.tar.xz -C libsilkit-${SILKIT_VERSION}
    ret_val=$?
    if [ "$ret_val" != '0' ] ; then
        echo "SILKIT-PKG: Could not untar orig tarball $orig_tarball"
        exit 64
    fi
    orig_found=true
fi

# Check git before https/ftp
if ! $orig_found ; then

    if git ls-remote -hq ${SILKIT_SOURCE_URL} ; then
        #git -c http.sslVerify=false clone ${SILKIT_SOURCE_URL} --depth=1 -b "sil-kit/v${SILKIT_VERSION}" libsilkit-${SILKIT_VERSION}
        git -c http.sslVerify=false clone ${SILKIT_SOURCE_URL} --depth=1 -b "main" libsilkit-${SILKIT_VERSION}
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
fi

# Check wgettable orig
if ! $orig_found ; then

    if wget -q --method=HEAD ${SILKIT_SOURCE_URL} ; then
        orig_tarball=$SILKIT_SOURCE_URL
        wget --no-proxy --no-check-certificate $orig_tarball
        orig_found=true

        mkdir -p libsilkit-${SILKIT_VERSION}
        tar -xvf libsilkit_${SILKIT_VERSION}.orig.tar.xz -C libsilkit-${SILKIT_VERSION}
        ret_val=$?
        if [ "$ret_val" != '0' ] ; then
            echo "SILKIT-PKG: Could not untar orig tarball $orig_tarball"
            exit 64
        fi
    fi
    echo "SILKIT-PKG: USED HTTPS BITCHES!"
fi

if ! $orig_found ; then
    echo "SILKIT-PKG: Could not get the orig tarball. Exiting!"
    exit 128
fi


debian_path="${SILKIT_PKG_URL}"
silkit_pkg_found=false
if [ -d ${SILKIT_PKG_URL} ] ; then
    silkit_pkg_found=true
fi

if ! $silkit_pkg_found ; then
    if git ls-remote -hq ${SILKIT_PKG_URL} ; then
        git -c http.sslVerify=false clone --depth=1 ${SILKIT_PKG_URL} -b ${SILKIT_PKG_BRANCH} sil-kit-pkg
        ret_val=$?
        if [ "$ret_val" != '0' ] ; then
            echo "SILKIT-PKG: Could not clone $SILKIT_PKG_REPO : $SILKIT_PKG_BRANCH"
            exit 64
        fi
        debian_path="./sil-kit-pkg"
    fi
fi

SILKIT_PACKAGE_REPO_NAME=$(echo ${SILKIT_PACKAGING_REPO} | awk -F/ '{print $NF}' | awk -F. '{print $1}')
echo "PACKAGING REPO NAME ${SILKIT_PACKAGE_REPO_NAME}"
cp -r ${debian_path}/debian libsilkit-${SILKIT_VERSION}

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
