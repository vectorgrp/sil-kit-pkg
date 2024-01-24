FROM debian:sid

ENV TZ "Europe/Berlin"
ENV DEBIAN_FRONTEND "noninteractive"
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN     apt update \
    &&  apt -y install \
            sudo \
            build-essential \
            debhelper \
            devscripts \
            dh-make \
            dh-cmake \
            \
            ninja-build \
            \
            libfmt-dev \
            libspdlog-dev \
            libasio-dev \
            libyaml-cpp-dev \
            wget \
            libgtest-dev \
            libgmock-dev \
    &&  true

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

