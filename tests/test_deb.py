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
import tarfile

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
    ap.add_argument("--distro-version", type=int, required=True)
    ap.add_argument("--package-format", type=str, choices=["deb", "rpm", "tgz"], required=False,
                    help="Defaults to deb on ubuntu and rpm on fedora")
    return ap

def as_root(args):
    return args if os.geteuid() == 0 else ['sudo'] + args

def install_debs(deb_directory):

    print("\nInstall SilKit Ubuntu packages")
    print("--------------------------------\n", flush=True)
    debs = deb_directory.glob('*.deb')
    str_args = [str(deb.resolve()) for deb in debs]
    args = as_root(['apt', 'install', '-y'] + str_args)

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

def extract_tarball(tgz_directory, test_dir) -> Path:
    """Extract the binary tarball (not the .debug one) and return its root directory."""

    print("\nExtract SilKit tarball")
    print("--------------------------------\n", flush=True)
    tarballs = [t for t in tgz_directory.glob('libsilkit-*.tar.gz') if not t.name.endswith('.debug.tar.gz')]
    debug_tarballs = list(tgz_directory.glob('libsilkit-*.debug.tar.gz'))
    if len(tarballs) != 1 or len(debug_tarballs) != 1:
        print(f"Expected one tarball and one debug tarball in {tgz_directory}, found {tarballs} and {debug_tarballs}")
        exit(64)

    extract_dir = (test_dir / '_pkg').resolve()
    subprocess.run(['rm', '-rf', str(extract_dir)], check=True)
    extract_dir.mkdir()
    for tarball in tarballs + debug_tarballs:
        with tarfile.open(tarball) as tar:
            tar.extractall(extract_dir)

    root = extract_dir / tarballs[0].name[:-len('.tar.gz')]
    debug_root = extract_dir / debug_tarballs[0].name[:-len('.tar.gz')]
    if not (root / 'bin' / 'sil-kit-registry').exists():
        print(f"{root} does not contain bin/sil-kit-registry")
        exit(64)
    if not list((debug_root / 'lib' / 'debug' / '.build-id').glob('*/*.debug')):
        print(f"{debug_root} does not contain any debug files")
        exit(64)
    return root

def run_registry(registry_cmd='sil-kit-registry'):

    print("\nRun sil-kit-registry")
    print("--------------------------------\n", flush=True)
    registry_proc = subprocess.Popen(registry_cmd, shell=False)
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

def build_test(test_dir, distro: str, distro_version: int, prefix_path: Optional[Path] = None):

    cc = "clang-10" if distro.lower() == "ubuntu" and distro_version < 22 else "clang"
    cxx = "clang++-10" if distro.lower() == "ubuntu" and distro_version < 22 else "clang++"
    cc = os.environ.get("CC", cc)
    cxx = os.environ.get("CXX", cxx)

    print("\nBuild the SilKit Test program")
    print(f"Using {cc} and {cxx}")
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
    cmake_args = ['cmake', '-GNinja', '../']
    if prefix_path is not None:
        cmake_args.append(f'-DCMAKE_PREFIX_PATH={prefix_path}')
    subprocess.run(cmake_args, env=current_env, cwd=build_dir, check=True)

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

    package_format = args.package_format
    if package_format is None:
        package_format = {"ubuntu": "deb", "fedora": "rpm"}.get(args.distro.lower())

    test_dir = args.test_directory
    prefix_path = None
    registry_cmd = 'sil-kit-registry'

    # Check package install
    if package_format == "deb":
        install_debs(args.package_directory)
    elif package_format == "rpm":
        install_rpms(args.package_directory)
    elif package_format == "tgz":
        prefix_path = extract_tarball(args.package_directory, test_dir)
        registry_cmd = str(prefix_path / 'bin' / 'sil-kit-registry')
    else:
        print(f"{args.distro} is currently not supported. Exiting!")
        exit(64)


    # Check demo program (compilation/link/execution)
    build_dir = test_dir / '_build'
    build_test(test_dir, args.distro, args.distro_version, prefix_path)
    registry = run_registry(registry_cmd)
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
