import gzip
import logging
import os
import re
import shutil
import subprocess
import tarfile

from pathlib import Path

from silkit_pkg_interface import SilKitPKG
from silkit_pkg_utils import BuildInfo, BuildFlags
from silkit_pkg_utils import get_global_loglevel, get_global_formatting

###############################################################################
logger = logging.getLogger("TGZBuilder")
console_handler = logging.StreamHandler()
console_handler.setLevel(get_global_loglevel())
console_handler.setFormatter(logging.Formatter(get_global_formatting()))
logger.addHandler(console_handler)
logger.propagate = False


class SilKitTGZ(SilKitPKG):
    """Relocatable binary tarball plus a separate debug symbol tarball.

    Layout of libsilkit-<version>.<platform>.x86_64.tar.gz:
        bin/, lib/ (libSilKit.so*, cmake/SilKit), include/, share/man/man1/,
        share/sil-kit/sil-kit-registry.service, share/doc/libsilkit/
    Layout of libsilkit-<version>.<platform>.x86_64.debug.tar.gz:
        lib/debug/.build-id/xx/yyyy.debug
    """

    def __init__(self, build_info: BuildInfo):
        g_loglevel = get_global_loglevel()
        if logger.level != g_loglevel:
            # Update loglevel, not perfect but works
            logger.setLevel(g_loglevel)
            console_handler.setLevel(g_loglevel)
        logger.debug("Creating TGZBuilder Instance")
        self.build_info = build_info

    def get_buildinfo(self):
        return self.build_info

    def source_dir_name(self):
        silkit_version = self.build_info.version
        return f"libsilkit{silkit_version.major}-{str(silkit_version)}"

    def package_name(self):
        # '~' is not kept by GitHub release assets, use '-' for suffixes like rc1
        version = str(self.build_info.version).replace("~", "-")
        return f"libsilkit-{version}.{self.build_info.platform}.x86_64"

    def setup_build_env(self):
        self.build_flags = SilKitTGZ.__get_build_flags(self.build_info.platform)
        logger.info(f"Got build_flags: {self.build_flags}")

        work_dir = self.build_info.work_dir.resolve()
        self.source_dir = work_dir / self.source_dir_name()
        self.build_dir = work_dir / "_build_tgz"
        self.stage_dir = work_dir / "_stage_tgz" / self.package_name()
        self.debug_stage_dir = work_dir / "_stage_tgz_debug" / (self.package_name() + ".debug")

        for d in (self.build_dir, self.stage_dir.parent, self.debug_stage_dir.parent):
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True)

        self.source_date_epoch = self.__source_date_epoch()
        logger.info(f"SOURCE_DATE_EPOCH={self.source_date_epoch}")

    def build(self):
        try:
            self.__configure()
            self.__run(["cmake", "--build", str(self.build_dir)])
            self.__run(["ctest", "--output-on-failure", "-R", "^(I|T)", "--test-dir", str(self.build_dir)])
            self.__run(["cmake", "--install", str(self.build_dir), "--prefix", str(self.stage_dir)])
            self.__split_debug_info()
            self.__add_extra_files()
            self.__pack(self.stage_dir, self.build_info.work_dir / (self.package_name() + ".tar.gz"))
            self.__pack(self.debug_stage_dir, self.build_info.work_dir / (self.package_name() + ".debug.tar.gz"))
        except RuntimeError:
            raise
        except Exception as ex:
            raise RuntimeError("Error while building the tarball") from ex

    def copy_artifacts(self):
        try:
            Path.mkdir(self.build_info.output_dir, parents=True, exist_ok=True)
        except Exception as ex:
            logger.error(f"Cannot create output dir {self.build_info.output_dir}")
            logger.error(f"mkdir: {str(ex)}")
            return

        for suffix in (".tar.gz", ".debug.tar.gz"):
            shutil.copy2(self.build_info.work_dir / (self.package_name() + suffix), self.build_info.output_dir)

    ###########################################################################

    def __run(self, cmd, **kwargs):
        logger.debug(f"Calling: {' '.join(cmd)}")
        try:
            return subprocess.run(cmd, check=True, **kwargs)
        except subprocess.CalledProcessError as ex:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}") from ex

    def __source_date_epoch(self) -> int:
        epoch = os.environ.get("SOURCE_DATE_EPOCH")
        if epoch:
            return int(epoch)
        # Fall back to the commit time of the sil-kit sources
        result = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", str(self.source_dir), "log", "-1", "--format=%ct"],
            check=False,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise RuntimeError("SOURCE_DATE_EPOCH is not set and the sil-kit sources have no git history")
        return int(result.stdout.strip())

    def __configure(self):
        # Map the build paths away so they do not end up in the binaries
        prefix_map = f"-ffile-prefix-map={self.source_dir}=. -ffile-prefix-map={self.build_dir}=."
        flags = f"-gdwarf-4 {prefix_map} {self.build_flags.add_platform_flags}".strip()

        env = os.environ.copy()
        env["CFLAGS"] = flags
        env["CXXFLAGS"] = flags
        env["SOURCE_DATE_EPOCH"] = str(self.source_date_epoch)

        self.__run(
            [
                "cmake",
                "-S", str(self.source_dir),
                "-B", str(self.build_dir),
                "-GNinja",
                "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                f"-DCMAKE_C_COMPILER={self.build_flags.c_compiler}",
                f"-DCMAKE_CXX_COMPILER={self.build_flags.cxx_compiler}",
                "-DCMAKE_INSTALL_LIBDIR=lib",
                "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
                "-DSILKIT_BUILD_LINUX_PACKAGE=ON",
                "-DSILKIT_BUILD_DEMOS=OFF",
                "-DSILKIT_INSTALL_SOURCE=OFF",
            ],
            env=env,
        )

    def __elf_files(self):
        for path in sorted(self.stage_dir.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            with open(path, "rb") as f:
                if f.read(4) == b"\x7fELF":
                    yield path

    def __build_id(self, path: Path) -> str:
        notes = subprocess.run(
            ["readelf", "-n", str(path)], check=True, stdout=subprocess.PIPE, universal_newlines=True
        ).stdout
        match = re.search(r"Build ID:\s*([0-9a-f]+)", notes)
        if not match:
            raise RuntimeError(f"{path} has no build ID, cannot place its debug info")
        return match.group(1)

    def __split_debug_info(self):
        for elf in self.__elf_files():
            logger.info(f"Splitting debug info off {elf.relative_to(self.stage_dir)}")
            # dwz is an optimization only; it refuses some inputs, that is fine
            subprocess.run(["dwz", "-q", str(elf)], check=False)

            build_id = self.__build_id(elf)
            debug_file = (
                self.debug_stage_dir / "lib" / "debug" / ".build-id" / build_id[:2] / (build_id[2:] + ".debug")
            )
            debug_file.parent.mkdir(parents=True, exist_ok=True)

            self.__run(["objcopy", "--only-keep-debug", "--compress-debug-sections=zlib", str(elf), str(debug_file)])
            debug_file.chmod(0o644)
            self.__run(
                [
                    "objcopy",
                    "--strip-debug",
                    "--strip-unneeded",
                    f"--add-gnu-debuglink={debug_file}",
                    str(elf),
                ]
            )

    def __find_changelog(self) -> Path:
        version = self.build_info.version
        versions_dir = self.source_dir / "docs" / "changelog" / "versions"
        plain_version = f"{version.major}.{version.minor}.{version.patch}"

        changelog = versions_dir / f"{plain_version}.md"
        if not changelog.exists():
            # During release preparation the entry still lives in latest.md
            changelog = versions_dir / "latest.md"

        with open(changelog, "r", encoding="utf-8") as f:
            header = f.readline()
        match = re.match(r"^#\s*\[([0-9]+\.[0-9]+\.[0-9]+)\]", header)
        if not match or match.group(1) != plain_version:
            raise RuntimeError(f"{changelog} does not describe version {plain_version}: {header.strip()}")
        return changelog

    def __add_extra_files(self):
        pkg_path = self.build_info.silkit_pkg_path.expanduser()

        service_dir = self.stage_dir / "share" / "sil-kit"
        service_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pkg_path / "rpm" / "sil-kit-registry.service", service_dir / "sil-kit-registry.service")

        # cmake installs LICENSE and README only with SILKIT_INSTALL_SOURCE=ON
        doc_dir = self.stage_dir / "share" / "doc" / "libsilkit"
        doc_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.source_dir / "LICENSE", doc_dir / "LICENSE")
        shutil.copy2(self.source_dir / "README.rst", doc_dir / "README.rst")
        shutil.copy2(self.__find_changelog(), doc_dir / "CHANGELOG.md")

    def __pack(self, stage_dir: Path, archive: Path):
        """Reproducible tar.gz: sorted entries, root ownership, normalized modes,
        mtime = SOURCE_DATE_EPOCH, and no name or time in the gzip header."""

        epoch = self.source_date_epoch

        def normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = epoch
            if info.isdir():
                info.mode = 0o755
            elif info.isfile():
                info.mode = 0o755 if info.mode & 0o111 else 0o644
            return info

        logger.info(f"Packing {archive.name}")
        with open(archive, "wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
                with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tar:
                    # add() recurses in sorted order (Python >= 3.7)
                    tar.add(str(stage_dir), arcname=stage_dir.name, filter=normalize)

    @staticmethod
    def __get_build_flags(platform: str) -> BuildFlags:
        logger.info(f"Building for platform: {platform}")

        def env_or(name, default):
            return os.environ.get(name, default)

        if platform == "ubuntu2004":
            return BuildFlags(
                add_platform_flags="",
                add_debuild_flags=[],
                c_compiler=env_or("CC", "gcc"),
                cxx_compiler=env_or("CXX", "g++"),
            )

        if platform == "el7":
            return BuildFlags(
                add_platform_flags="",
                add_debuild_flags=[],
                c_compiler=env_or("CC", "/opt/rh/devtoolset-11/root/usr/bin/gcc"),
                cxx_compiler=env_or("CXX", "/opt/rh/devtoolset-11/root/usr/bin/g++"),
            )

        if platform == "el8":
            return BuildFlags(
                add_platform_flags="",
                add_debuild_flags=[],
                c_compiler=env_or("CC", "/opt/rh/gcc-toolset-12/root/usr/bin/gcc"),
                cxx_compiler=env_or("CXX", "/opt/rh/gcc-toolset-12/root/usr/bin/g++"),
            )

        raise RuntimeError(f"Unknown tarball platform: {platform}")
