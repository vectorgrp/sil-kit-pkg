#! /bin/env python3
import argparse
import json
import logging
import shutil
import subprocess
import re

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SilKitVersion:
    major: int
    minor: int
    patch: int
    suffix: str

@dataclass
class SilKitInfo:
    silkit_source_url: str
    silkit_source_ref: str
    silkit_source_path: Path
    is_local: bool
    recursive: bool

@dataclass
class BuildInfo:

    silkit_pkg_path: Path
    silkit_info: SilKitInfo
    version: SilKitVersion
    platform: str
    work_dir: Path
    keep_temp: bool
    output_dir: Path

@dataclass
class BuildFlags:
    add_platform_flags: str
    add_debuild_flags: str
    c_compiler: str
    cxx_compiler: str

logger = logging.getLogger("build_deb")

def create_arg_parser() -> ArgumentParser:
    ap = ArgumentParser("BuildPackages")
    ap.add_argument("--build-cfg", type=Path, required=True)
    ap.add_argument("--verbose", "-v", action='store_true', required=False)

    return ap

def load_cfg(cfg_path: Path):

    with open(cfg_path, 'r') as f:
        obj = json.load(f)
        logger.debug(f"Build config: \n{obj}")
        return obj

def cleanup(build_info: BuildInfo):

    silkit_info = build_info.silkit_info
    if silkit_info.is_local == False and silkit_info.silkit_source_path != None:
        shutil.rmtree(silkit_info.silkit_source_path, ignore_errors=True)

    if build_info.work_dir != None and build_info.keep_temp == False:
        shutil.rmtree(build_info.work_dir.resolve())

def die(build_info: BuildInfo, exitCode: int):
    cleanup(build_info)
    exit(exitCode)

def generate_buildinfo(cfg) -> BuildInfo:

    silkit_info = SilKitInfo(
                silkit_source_url=cfg["SilKitInfo"]["url"],
                silkit_source_ref=cfg["SilKitInfo"]["ref"],
                is_local=cfg["SilKitInfo"]["is_local"],
                recursive=cfg["SilKitInfo"]["recursive"],
                silkit_source_path=None)

    silkit_version = SilKitVersion(
            major=cfg["version"]["major"],
            minor=cfg["version"]["minor"],
            patch=cfg["version"]["patch"],
            suffix=cfg["version"]["suffix"])

    build_info = BuildInfo(
            silkit_pkg_path=Path(cfg["package_repo_path"]),
            silkit_info=silkit_info,
            version=silkit_version,
            work_dir=Path(cfg["work_dir"]),
            keep_temp=cfg["keep_temp"],
            output_dir=Path(cfg["output_dir"]),
            platform=cfg["platform"]
    )
    logger.debug(f"build_info: {build_info}")
    return build_info

def clone_silkit(build_info: BuildInfo):
    repoUrl = build_info.silkit_info.silkit_source_url
    repoPath = build_info.work_dir / 'sil-kit'
    repoRef = build_info.silkit_info.silkit_source_ref
    try:
        build_info.silkit_info.silkit_source_path = repoPath
        subprocess.run(['git', 'init', repoPath], check=True)
        subprocess.run(['git', 'remote', 'add', 'origin', build_info.silkit_info.silkit_source_url],
                       cwd=repoPath,
                       check=True)
        result = subprocess.run(['git', 'fetch', '--no-tags', '--prune',
                        '--no-recurse-submodules', '--depth=1', 'origin',
                        repoRef],
                                cwd=repoPath,
                                check=True)
        subprocess.run(['git', 'checkout', '--progress', '--force', repoRef],
                       cwd=repoPath,
                       check=True)

        if build_info.silkit_info.recursive == True:
            logger.debug("Syncing the submodules!")
            subprocess.run(['git', 'submodule', 'sync', '--recursive'],
                           cwd=repoPath,
                           check=True)
            subprocess.run(['git', 'submodule', 'update', '--init', '--depth=1', '--recursive'],
                           cwd=repoPath,
                           check=True)

    except Exception as ex:
        logger.error(f"While cloning the SilKit Repo something occured: {str(ex)}")
        die(build_info, 64)


def get_silkit_repo(build_info: BuildInfo):

    # Check whether the repo is already checked out!
    repoPath = Path(build_info.silkit_info.silkit_source_url)
    logger.debug(f"Checking {repoPath}")

    if repoPath.exists():

        git_dir = repoPath / '.git'

        if not git_dir.exists():
            logger.error("The sil-kit path does exist, but is no GIT repo! Exiting!")
            die(build_info, 64)

        # Copy sil-kit-dir
        try:
            shutil.copytree(repoPath, build_info.work_dir / repoPath)
        except Exception as ex:
            logger.error("Could not copy the sil-kit source tree into the workspace dir! Exiting")
            logger.debug(f"Python Exception: {str(ex)}")
            die(build_info, 64)

        build_info.silkit_info.silkit_source_path = repoPath
        build_info.silkit_info.is_local = True
    else:
        clone_silkit(build_info)

def check_debian_directory(build_info: BuildInfo):

    debian_path = build_info.silkit_pkg_path / 'debian'
    logger.debug(f"Checking {debian_path.expanduser()}")
    if not debian_path.expanduser().exists():
        logger.error("The sil-kit-pkg/debian path does not exist! Exiting!")
        die(build_info, 64)
    else:
        logger.info("Found the debian dir!")

def get_deb_version(build_info: BuildInfo):

    pattern = re.compile('^libsilkit \(([0-9]+)\.([0-9]+)\.([0-9]+)-([0-9]+).*')

    changelog_path = build_info.silkit_pkg_path.expanduser() / 'debian/changelog'
    logger.debug(f"Checking {changelog_path}")
    if not changelog_path.expanduser().exists():
        logger.error("Could not find Package Changelog! Exiting!")
        die(build_info, 64)

    with open(changelog_path) as f:
        for line in f:
            result = re.match(pattern, line)
            if result:
                build_info.version = SilKitVersion(
                    major=result.group(1),
                    minor=result.group(2),
                    patch=result.group(3),
                    suffix=result.group(4))

            logger.debug(f'SilKitVersion: {build_info.version}')
            return

def create_work_directory(build_info: BuildInfo) -> Path:

    work_dir = Path.cwd() / build_info.work_dir;
    logger.debug(f"Creating {work_dir} work dir!")

    try:
        Path.mkdir(work_dir, exist_ok=True)
    except Exception as ex:
        logger.error(f"While creating the workdir an error occured: {str(ex)}")
        # No need for cleanup, nothing of value created yet
        exit(64)

def create_orig_tarball(build_info: BuildInfo):

    silkit_version = build_info.version

    if silkit_version == None:
        logger.error("No valid SilKit Version found! Exiting!")
        die(build_info, 64)

    tarball_name = 'libsilkit_{}.{}.{}.orig.tar.gz'.format(
            silkit_version.major,
            silkit_version.minor,
            silkit_version.patch)
    try:
        subprocess.run(['tar', '--exclude=.git', '-czf', build_info.work_dir/tarball_name,
                        '-C', build_info.silkit_info.silkit_source_path, '.'], check=True)
    except Exception as ex:
        logger.error(f"While creating the orig tarball, an error occured!\n{str(ex)}")
        die(build_info, 64)

def copy_debian_dir(build_info: BuildInfo):

    # Copy debian dir
    try:
        shutil.copytree(build_info.silkit_pkg_path.expanduser() / 'debian/', build_info.work_dir / 'sil-kit/debian')
    except Exception as ex:
        logger.error("Could not copy the debian dir into the sil kit source dir! Exiting")
        logger.debug(f"Python Exception: {str(ex)}")
        die(build_info, 64)

def parse_platform(platform: str) -> str:

    dist, version = platform.split('-')
    logger.info(f"Building for {dist} version {version}")

    return version


def get_build_flags(ubuntu_version: str) -> BuildFlags:

    logger.info(f"Building for platform: {ubuntu_version}")
    if ubuntu_version == "20.04":
        return BuildFlags(
                add_platform_flags="",
                add_debuild_flags="-d --prepend-path=/opt/vector/bin",
                c_compiler="clang-10",
                cxx_compiler="clang++-10")
    if ubuntu_version == "22.04":
        return BuildFlags(
                add_platform_flags="-gdwarf-4",
                add_debuild_flags="",
                c_compiler="clang",
                cxx_compiler="clang++")
    if ubuntu_version == "24.04":
        return BuildFlags(
                add_platform_flags="",
                add_debuild_flags="",
                c_compiler="clang",
                cxx_compiler="clang++")

    return None

def build_package(build_flags: BuildFlags, build_info: BuildInfo):

    platform_build_flags = f'--set-envvar=PLATFORM_BUILD_FLAGS={build_flags.add_platform_flags}' if build_flags.add_platform_flags != '' else ''

    debuild_flags = build_flags.add_debuild_flags.split(' ')
    logger.debug(f"Additional debuild flags: {debuild_flags}")
    debuild_cmd = ['debuild'] + debuild_flags + [platform_build_flags,
                f'--set-envvar=CC={build_flags.c_compiler}',
                f'--set-envvar=CXX={build_flags.cxx_compiler}',
                '-us',
                '-uc',
                '--lintian-opts',
                '-E',
                '--pedantic']

    # If we have '' empty strings in the command list, strange things happen in
    # exec land
    debuild_cmd = list(filter(lambda arg: arg != '', debuild_cmd))

    logger.debug(f"CMD LIST: {debuild_cmd}")
    logger.debug(f"Calling: {' '.join(debuild_cmd)}")
    subprocess.run(debuild_cmd,
                check=True,
                cwd=build_info.work_dir / 'sil-kit/')

def copy_artifacts(build_info: BuildInfo):

    try:
        Path.mkdir(build_info.output_dir, exist_ok=True)
    except Exception as ex:
        logger.error(f"Cannot create output dir {build_info.output_dir}")
        logger.error(f"mkdir: {str(ex)}")
        return

    file_list = (p.resolve() for p in build_info.work_dir.iterdir() if re.search(r"(.*\.build.*$)|(.*\.changes$)|(.*\..*deb$)|(.*\.dsc$)", p.suffix))

    for file in file_list:
        shutil.copy2(file, build_info.output_dir)

def main():
    arg_parser = create_arg_parser()
    args =arg_parser.parse_args()

    level = logging.INFO;
    log_fmt = '%(asctime)s %(name)s %(levelname)s: %(message)s'
    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(level=level, format=log_fmt)

    cfg = load_cfg(args.build_cfg)
    build_info = generate_buildinfo(cfg)

    create_work_directory(build_info)
    get_silkit_repo(build_info)
    check_debian_directory(build_info)
    #get_deb_version(build_info)
    create_orig_tarball(build_info)
    copy_debian_dir(build_info)
    build_flags = get_build_flags(parse_platform(build_info.platform))
    logger.info(f"Got build_flags: {build_flags}")
    build_package(build_flags, build_info)
    copy_artifacts(build_info)
    cleanup(build_info)
    exit(0)

if __name__ == '__main__':
    main()

