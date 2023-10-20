FROM debian:sid

RUN apt-get update
RUN apt-get install -y build-essential ninja-build cmake \
        libyaml-cpp-dev libasio-dev libfmt-dev libspdlog-dev \
        devscripts dh-cmake lld dh-make wget

ENV USER=root

ENTRYPOINT ["./.github/actions/build_deb.sh"]
