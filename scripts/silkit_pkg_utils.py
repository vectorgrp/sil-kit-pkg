from dataclasses import dataclass
from pathlib import Path
import subprocess
import logging


###############################################################################
## Util Dataclasses
###############################################################################
@dataclass
class SilKitVersion:
    major: int
    minor: int
    patch: int
    suffix: str

    def __str__(self):
        version_str = f"{self.major}.{self.minor}.{self.patch}"

        if self.suffix != None and self.suffix != "":
            version_str = version_str + f"~{self.suffix}"

        return version_str


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
    pkgformat: str
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


###############################################################################
## Util Functions
###############################################################################
loglevel = logging.INFO


def set_global_loglevel(level):
    global loglevel
    loglevel = level


def get_global_loglevel():
    return loglevel


def get_global_formatting():
    return "%(asctime)s %(name)s %(levelname)s: %(message)s"
