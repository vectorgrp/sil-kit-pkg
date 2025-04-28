import logging
import shutil
import subprocess
import re
import os

from pathlib import Path

from silkit_pkg_interface import SilKitPKG
from silkit_pkg_utils import BuildInfo, SilKitVersion, SilKitInfo, BuildFlags
from silkit_pkg_utils import get_global_loglevel, get_global_formatting

###############################################################################
logger = logging.getLogger("DEBBuilder")
console_handler = logging.StreamHandler()
console_handler.setLevel(get_global_loglevel())
console_handler.setFormatter(logging.Formatter(get_global_formatting()))
logger.addHandler(console_handler)
logger.propagate = False


class SilKitDEB(SilKitPKG):

    def __init__(self, build_info: BuildInfo):
        g_loglevel = get_global_loglevel()
        if logger.level != g_loglevel:
            # Update loglevel, not perfect but works
            logger.setLevel(g_loglevel)
            console_handler.setLevel(g_loglevel)
        logger.debug("Creating DEBBuilder Instance")
        self.build_info = build_info

    def copy_artifacts(self):
        suffixes = r"(.*\.build.*$)|(.*\.changes$)|(.*\..*deb$)|(.*\.dsc$)"
        try:
            Path.mkdir(self.build_info.output_dir, exist_ok=True)
        except Exception as ex:
            logger.error(f"Cannot create output dir {self.build_info.output_dir}")
            logger.error(f"mkdir: {str(ex)}")
            return

        file_list = (
            p.resolve() for p in self.build_info.work_dir.iterdir() if re.search(suffixes, p.suffix)
        )

        for file in file_list:
            shutil.copy2(file, self.build_info.output_dir)

    def get_buildinfo(self):
        return self.build_info

    def source_dir_name(self):
        silkit_version = self.build_info.version
        source_dir = f"libsilkit{silkit_version.major}-{str(silkit_version)}"
        return source_dir

    def setup_build_env(self):
        try:
            self.__check_debian_directory()
            self.__create_orig_tarball()
            self.__copy_debian_dir()
        except RuntimeError as rte:
            raise

    def build(self):

        try:
            build_flags = SilKitDEB.__get_debian_build_flags(self.__parse_platform())
            logger.info(f"Got build_flags: {build_flags}")
            self.__build_package(build_flags)
        except RuntimeError as rte:
            raise
        except Exception as ex:
            raise RuntimeError("Error while building the package") from ex

    def __check_debian_directory(self):
        debian_path = self.build_info.silkit_pkg_path / "debian"
        logger.debug(f"Checking {debian_path.expanduser()}")
        if not debian_path.expanduser().exists():
            raise RuntimeError("The sil-kit-pkg/debian path does not exist!")
        else:
            logger.info("Found the debian dir!")

    def __create_orig_tarball(self):
        silkit_version = self.build_info.version

        if silkit_version == None:
            raise RuntimeError("No valid SilKit Version found! Exiting!")

        tarball_name = f"libsilkit_{str(silkit_version)}.orig.tar.gz"
        try:
            subprocess.run(
                [
                    "tar",
                    "--exclude=.git",
                    "-czf",
                    self.build_info.work_dir / tarball_name,
                    "-C",
                    self.build_info.work_dir,
                    self.source_dir_name(),
                ],
                check=True,
            )
        except Exception as ex:
            raise RuntimeError(f"While creating the Source tarball, an error occured!") from ex

    def __copy_debian_dir(self):
        try:
            shutil.copytree(
                self.build_info.silkit_pkg_path.expanduser() / "debian/",
                self.build_info.work_dir / self.source_dir_name() / "debian",
            )
        except Exception as ex:
            logger.error("Could not copy the debian dir into the sil kit source dir! Exiting")
            raise RuntimeError("Could not copy the debian directory") from ex

    def __parse_platform(self) -> str:

        dist, version = self.build_info.platform.split("-")
        logger.info(f"Building for {dist} version {version}")

        return version

    def __build_package(self, build_flags: BuildFlags):

        try:
            platform_build_flags = (
                f"--set-envvar=PLATFORM_BUILD_FLAGS={build_flags.add_platform_flags}"
                if build_flags.add_platform_flags != ""
                else ""
            )

            debuild_flags = [*build_flags.add_debuild_flags, *self.build_info.debuild.args]

            logger.debug(f"Additional debuild flags: {debuild_flags}")
            debuild_cmd = (
                ["debuild"]
                + debuild_flags
                + [
                    platform_build_flags,
                    f"--set-envvar=CC={build_flags.c_compiler}",
                    f"--set-envvar=CXX={build_flags.cxx_compiler}",
                    "-us",
                    "-uc",
                    "--lintian-opts",
                    "-E",
                    "--pedantic",
                ]
            )

            # If we have '' empty strings in the command list, strange things happen in
            # exec land
            debuild_cmd = list(filter(lambda arg: arg != "", debuild_cmd))

            logger.debug(f"CMD LIST: {debuild_cmd}")
            logger.debug(f"Calling: {' '.join(debuild_cmd)}")
            subprocess.run(debuild_cmd, check=True, cwd=self.build_info.work_dir / self.source_dir_name())
        except Exception as ex:
            raise RuntimeError("debuild command failed") from ex

    @staticmethod
    def __get_debian_build_flags(ubuntu_version: str) -> BuildFlags:
        logger.info(f"Building for platform: {ubuntu_version}")

        def env_or(name, default):
            return os.environ.get(name, default)

        if ubuntu_version == "20.04":
            return BuildFlags(
                add_platform_flags="-gdwarf-4",
                add_debuild_flags=[],
                c_compiler=env_or("CC", "clang"),
                cxx_compiler=env_or("CXX", "clang++"),
            )

        if ubuntu_version == "22.04":
            return BuildFlags(
                add_platform_flags="-gdwarf-4",
                add_debuild_flags=[],
                c_compiler=env_or("CC", "clang"),
                cxx_compiler=env_or("CXX", "clang++"),
            )

        if ubuntu_version == "24.04":
            return BuildFlags(
                add_platform_flags="-gdwarf-4",
                add_debuild_flags=[],
                c_compiler=env_or("CC", "clang"),
                cxx_compiler=env_or("CXX", "clang++"),
            )

        return None
