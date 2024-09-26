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

    ap.add_argument("--deb-directory", type=Path, required=True)
    ap.add_argument("--package-directory", type=Path, required=True)
    return ap

def install_debs(deb_directory):

    print("\nInstall SilKit Ubuntu packages")
    print("--------------------------------\n", flush=True)
    debs = deb_directory.glob('*.deb')
    str_args = [str(deb.resolve()) for deb in debs]
    args = ['apt', 'install', '-y'] + str_args

    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        print("Could not install the DEB files. Exiting with ERROR!")
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

def build_test(test_dir):

    print("\nBuild the SilKit Test program")
    print("--------------------------------\n", flush=True)
    # Clean the workspace
    subprocess.run(['rm', '-rf', '_build'], cwd=test_dir, check=True)
    # Create the build dir
    subprocess.run(['mkdir', '_build'], cwd=test_dir)

    # Configure the build
    current_env = os.environ.copy()
    current_env["CC"]="clang-10"
    current_env["CXX"]="clang++-10"
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
        print("Test did not run to completion. Your problem now!")
        exit(64)

def main():
    argument_parser = create_arg_parser()
    args =argument_parser.parse_args()

    # Check deb install
    install_debs(args.deb_directory)
    registry = run_registry()

    # Check demo program (compilation/link/execution)
    test_dir = args.package_directory / 'tests'
    build_dir = test_dir / '_build'
    build_test(test_dir)
    run_test(build_dir)
    close_registry(registry)

if __name__ == "__main__":
    main()
