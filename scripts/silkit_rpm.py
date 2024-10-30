import glob
import logging
import shutil
import subprocess
import re

from pathlib import Path

from silkit_pkg_interface import SilKitPKG
from silkit_pkg_utils import BuildInfo, SilKitVersion, SilKitInfo
from silkit_pkg_utils import get_global_loglevel, get_global_formatting

###############################################################################
logger = logging.getLogger("RPMBuilder")
console_handler = logging.StreamHandler()
console_handler.setLevel(get_global_loglevel())
console_handler.setFormatter(logging.Formatter(get_global_formatting()))
logger.addHandler(console_handler)
logger.setLevel(get_global_loglevel())
logger.propagate = False


class SilKitRPM(SilKitPKG):

    def __init__(self, build_info: BuildInfo):

        g_loglevel = get_global_loglevel()
        if logger.level != g_loglevel:
            # Update loglevel, not perfect but works
            logger.setLevel(g_loglevel)
            console_handler.setLevel(g_loglevel)
        logger.debug("Creating the RPMBuilder")
        self.build_info = build_info

    @staticmethod
    def get_distro_abbr(distro_shortname: str) -> str:

        if distro_shortname == "epel":
            return "el"
        elif distro_shortname == "fedora":
            return "fc"
        else:
            return None

    def copy_artifacts(self):

        # File extensions of our finished packages
        suffixes = r"(.*\.rpm)"

        # Get the Distro Name + release
        dname, drelease = re.search(r"^(\w+)(\d)", self.build_info.platform).groups()
        logger.debug(f"Building for: {dname} {drelease}")

        distro_dir = self.get_distro_abbr(dname) + drelease
        artifacts_dir = (
            self.build_info.work_dir
            / f"results_libsilkit{self.build_info.version.major}"
            / str(self.build_info.version)
            / f"1.{distro_dir}"
        )
        try:
            Path.mkdir(self.build_info.output_dir, exist_ok=True)
        except Exception as ex:
            logger.error(f"Cannot create output dir {self.build_info.output_dir}")
            logger.error(f"mkdir: {str(ex)}")
            return

        file_list = (p.resolve() for p in artifacts_dir.iterdir() if re.search(suffixes, p.suffix))

        for file in file_list:
            shutil.copy2(file, self.build_info.output_dir)

    def get_buildinfo(self):
        return self.build_info

    def source_dir_name(self):
        silkit_version = self.build_info.version
        return "libsilkit{}-{}.{}.{}".format(
            silkit_version.major, silkit_version.major, silkit_version.minor, silkit_version.patch
        )

    def setup_build_env(self):
        try:
            self.__check_spec_file()
            self.__create_tarball()
            self.__copy_spec_files()
        except RuntimeError as rte:
            raise

    def build(self):

        fedpkg_cmd = ["fedpkg", f"--release={self.build_info.platform}", "mockbuild", "--", "--config-opts=print_main_output=True"]
        # If we have '' empty strings in the command list, strange things happen in
        # exec land
        fedpkg_cmd = list(filter(lambda arg: arg != "", fedpkg_cmd))

        logger.debug(f"Calling {' '.join(fedpkg_cmd)}")
        subprocess.run(fedpkg_cmd, check=True, cwd=self.build_info.work_dir, stderr=subprocess.STDOUT)

    def __check_spec_file(self):
        spec_dir = self.build_info.silkit_pkg_path / "rpm"
        logger.debug(f"Checking {spec_dir.expanduser()}")

        if not spec_dir.expanduser().exists():
            raise RuntimeError("The sil-kit-pkg/rpm path does not exist!")
        else:
            logger.info(f"Found the SPEC file dir: {spec_dir.expanduser()}")

    def __create_tarball(self):
        silkit_version = self.build_info.version

        if silkit_version == None:
            raise RuntimeError("No valid SilKit version found!")

        tarball_name = "libsilkit-{}.{}.{}.tar.gz".format(
            silkit_version.major, silkit_version.minor, silkit_version.patch
        )
        try:
            subprocess.run(
                [
                    "tar",
                    "--exclude=.git",
                    "-czf",
                    tarball_name,
                    self.build_info.silkit_info.silkit_source_path.name,
                ],
                check=True,
                cwd=self.build_info.work_dir,
            )
        except Exception as ex:
            raise RuntimeError(f"While creating the Source tarball, an error occured!") from ex

    def __copy_spec_files(self):
        try:
            globdir = self.build_info.silkit_pkg_path / "rpm"
            package_files = (
                p.resolve()
                for p in globdir.expanduser().glob("**/*")
                if p.suffix in {".spec", ".service"}
            )
            for f in package_files:
                logger.debug(f"Copying {f}")
                shutil.copy(globdir / f, self.build_info.work_dir)
        except Exception as ex:
            raise RuntimeError() from ex
