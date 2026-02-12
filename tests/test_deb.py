#! /bin/env python3
#
# SPDX-FileCopyrightText: 2024 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
import argparse
import logging
import os
import shlex
import subprocess
import signal

from argparse import ArgumentParser
from pathlib import Path
from time import sleep
from typing import Mapping, Optional

logger = logging.getLogger(__name__)

def create_arg_parser() -> ArgumentParser:
    ap = ArgumentParser("PackageTest")

    ap.add_argument("--package-directory", type=Path, required=True)
    ap.add_argument("--test-directory", type=Path, required=True)
    ap.add_argument("--distro", type=str, required=True)
    return ap

def install_debs(deb_directory):

    print("\nInstall SilKit Ubuntu packages")
    print("--------------------------------\n", flush=True)
    debs = deb_directory.glob('*.deb')
    str_args = [str(deb.resolve()) for deb in debs]
    args = ['sudo', 'apt', 'install', '-y'] + str_args

    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        print("Could not install the DEB files. Exiting with ERROR!")
        exit(64)

def install_rpms(rpm_directory):
    print("\nInstall SilKit Fedora/Alma Linux packages")
    print("--------------------------------\n", flush=True)
    rpms = rpm_directory.glob('*.x86_64.rpm')
    str_args = [str(rpm.resolve()) for rpm in rpms]
    args = ['dnf', 'install', '-y'] + str_args

    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        print("Could not install the RPM files. Exiting with ERROR!")
        exit(64)

def run_registry():

    print("\nRun sil-kit-registry")
    print("--------------------------------\n", flush=True)
    cmd = 'sil-kit-registry'
    registry_proc = subprocess.Popen(cmd, shell=False)
    sleep(2)

    if registry_proc.poll() != None:
        print("sil-kit-registry not started correctly! Exiting with ERROR!")
        exit(64)

    return registry_proc

def close_registry(reg_proc: subprocess.Popen):

    print("\nClose the SIL Kit registry")
    print("--------------------------------\n", flush=True)

    reg_proc.send_signal(signal.SIGINT)

    reg_proc.wait(5)
    if reg_proc.returncode != 0:
        print(f"sil-kit-registry did not terminate correctly ({reg_proc.returncode})! Exiting with ERROR!")
        exit(64)
    else:
        print("All is fine, exiting gracefully!")

def build_test(test_dir, distro: str):

    cc = "clang-10" if distro.lower() == "ubuntu" else "clang"
    cxx = "clang++-10" if distro.lower() == "ubuntu" else "clang++"

    print("\nBuild the SilKit Test program")
    print("--------------------------------\n", flush=True)
    # Clean the workspace
    subprocess.run(['rm', '-rf', '_build'], cwd=test_dir, check=True)
    # Create the build dir
    subprocess.run(['mkdir', '_build'], cwd=test_dir)

    # Configure the build
    current_env = os.environ.copy()
    current_env["CC"]=cc
    current_env["CXX"]=cxx
    build_dir = test_dir / '_build'
    subprocess.run(['cmake', '-GNinja', '../'], env=current_env, cwd=build_dir, check=True)

    # Build the test
    print(f"Build dir {build_dir}")
    ret = subprocess.run(['ninja'], env=current_env, cwd=build_dir, check=True)

def run_test(build_dir):

    print("\nRun the SilKit Test program")
    print("--------------------------------\n", flush=True)
    try:
        subprocess.run(['./Test'], cwd=build_dir, check=True)
    except:
        raise RuntimeError("Test did not run to completion. Your problem now!")

def main():
    argument_parser = create_arg_parser()
    args =argument_parser.parse_args()

    # Check deb install
    if args.distro.lower() == "ubuntu":
        install_debs(args.package_directory)
    elif args.distro.lower() == "fedora":
        install_rpms(args.package_directory)
    else:
        print(f"{args.distro} is currently not supported. Exiting!")
        exit(64)


    # Check demo program (compilation/link/execution)
    test_dir = args.test_directory
    build_dir = test_dir / '_build'
    build_test(test_dir, args.distro)
    registry = run_registry()
    ret_code = 0
    try:
        run_test(build_dir)
    except RuntimeError as rte:
        print(f"ERROR: {str(rte)}")
        ret_code = 64 

    close_registry(registry)
    exit(ret_code)

if __name__ == "__main__":
    main()
