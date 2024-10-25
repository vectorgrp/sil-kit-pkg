#! /bin/env python3
import argparse
import json
import logging
import re
import shutil
import subprocess
import traceback

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path

from silkit_pkg_utils import BuildInfo, SilKitVersion, SilKitInfo
from silkit_pkg_utils import set_global_loglevel, get_global_loglevel, get_global_formatting
from silkit_pkg_interface import SilKitPKG
from silkit_deb import SilKitDEB
from silkit_rpm import SilKitRPM

logger = logging.getLogger("SilKit Packaging")

def PkgClassFactory(build_info: BuildInfo) -> SilKitPKG:

    if build_info.pkgformat.lower() == "deb":
        return SilKitDEB(build_info)
    elif build_info.pkgformat.lower() == "rpm":
        return SilKitRPM(build_info)
    else:
        raise NotImplementedError(f"PKG format {build_info.pkgformat} is not implemented yet!")

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
        shutil.rmtree(build_info.work_dir.resolve(), ignore_errors=True)

def die(build_info: BuildInfo, exitCode: int):

    if logger.level == logging.DEBUG:
        traceback.print_exc()
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
            pkgformat=cfg["pkgformat"] if "pkgformat" in cfg else "",
            work_dir=Path(cfg["work_dir"]),
            keep_temp=cfg["keep_temp"],
            output_dir=Path(cfg["output_dir"]),
            platform=cfg["platform"]
    )
    logger.debug(f"build_info: {build_info}")
    return build_info

def clone_silkit(builder: SilKitPKG):

    build_info = builder.get_buildinfo()
    repoUrl = build_info.silkit_info.silkit_source_url
    repoPath = build_info.work_dir / builder.source_dir_name()
    repoRef = build_info.silkit_info.silkit_source_ref
    try:
        build_info.silkit_info.silkit_source_path = repoPath
        logger.debug(f"Initialize git repo at: {repoPath}")
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

            submodules = ["fmt", "spdlog", "googletest", "yaml-cpp", "asio"]

            logger.debug("Syncing the submodules!")

            for submodule in submodules:
                logger.debug(f"Syncing: {submodule}")
                subprocess.run(['git', 'submodule', 'sync', "ThirdParty/" + submodule],
                               cwd=repoPath,
                               check=True)
                subprocess.run(['git', 'submodule', 'update', '--init', '--depth=1', "ThirdParty/" + submodule],
                               cwd=repoPath,
                               check=True)

    except Exception as ex:
        logger.error(f"While cloning the SilKit Repo something occured: {str(ex)}")
        die(build_info, 64)


def get_silkit_repo(builder: SilKitPKG):

    # Check whether the repo is already checked out!
    build_info = builder.get_buildinfo()
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
        clone_silkit(builder)

def get_deb_version(build_info: BuildInfo):

    pattern = re.compile(r"^libsilkit \(([0-9]+)\.([0-9]+)\.([0-9]+)-([0-9]+).*")

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

def copy_artifacts(builder: SilKitPKG):
    builder.copy_artifacts()

def prepare_sources(builder: SilKitPKG):
        create_work_directory(builder.get_buildinfo())
        get_silkit_repo(builder)

def setup(builder: SilKitPKG):
    try:
        builder.setup_build_env()
    except RuntimeError as rte:
        logger.error(f"SilKitPKG setup error: {str(rte)}")
        die(builder.get_buildinfo(), 64)

def build(builder: SilKitPKG):
    try:
        builder.build()
    except RuntimeError as rte:
        logger.error(f"SilKitPKG build error: {str(rte)}")
        die(builder.get_buildinfo(), 64)

def main():
    arg_parser = create_arg_parser()
    args =arg_parser.parse_args()

    if args.verbose:
        set_global_loglevel(logging.DEBUG)

    level = get_global_loglevel();
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(get_global_formatting()))
    console_handler.setLevel(level)

    logger.addHandler(console_handler)
    logger.setLevel(level)
    logger.propagate = False

    cfg = load_cfg(args.build_cfg)
    build_info = generate_buildinfo(cfg)

    try:
        builder = PkgClassFactory(build_info)
    except NotImplementedError as nie:
        logger.error(f"SIL Kit PKG: {str(nie)}")
        die(build_info, 64)

    prepare_sources(builder)
    setup(builder)
    build(builder)
    copy_artifacts(builder)
    cleanup(build_info)
    exit(0)

if __name__ == '__main__':
    main()

