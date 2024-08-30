#
# SPDX-FileCopyrightText: 2024 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#

cmake_minimum_required(VERSION 3.12)
project("SilKit DEB Tests" LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)

find_package(SilKit
    REQUIRED
)

find_package(Threads
    REQUIRED
)

add_executable(Test test.cpp)
target_link_libraries(Test
    PRIVATE
        SilKit::SilKit
        Threads::Threads
)

