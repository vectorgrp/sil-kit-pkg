#! /bin/env python3
#
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
"""Check that debian/changelog, rpm/libsilkit5.spec and the sil-kit sources agree on the
version, and optionally that it matches the version delivery expects.

Prints major, minor, patch, suffix and version as key=value lines (GITHUB_OUTPUT format).
"""
import argparse
import re
import sys

from pathlib import Path


def read(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def deb_version(pkg_dir: Path):
    first_line = read(pkg_dir / "debian" / "changelog").splitlines()[0]
    match = re.match(r"libsilkit\s+\(([0-9]+)\.([0-9]+)\.([0-9]+)~*([A-Za-z]+[0-9]+)?-[0-9]+ubuntu[0-9]+\)", first_line)
    if not match:
        sys.exit(f"cannot parse the version from debian/changelog: {first_line}")
    return match.group(1), match.group(2), match.group(3), match.group(4) or ""


def rpm_version(pkg_dir: Path):
    spec = read(pkg_dir / "rpm" / "libsilkit5.spec")
    parts = []
    for component in ("major", "minor", "patch"):
        match = re.search(rf"^%define version_{component} ([0-9]+)\s*$", spec, re.MULTILINE)
        if not match:
            sys.exit(f"no version_{component} in rpm/libsilkit5.spec")
        parts.append(match.group(1))
    return tuple(parts)


def silkit_version(silkit_dir: Path):
    header = silkit_dir / "SilKit" / "include" / "silkit" / "capi" / "SilKitVersionMacros.h"
    if header.exists():
        text = read(header)
        pattern = r"^#define SILKIT_VERSION_{} ([0-9]+)\s*$"
    else:
        # sil-kit refs from before the version moved into SilKitVersionMacros.h
        text = read(silkit_dir / "SilKit" / "cmake" / "SilKitVersion.cmake")
        pattern = r"^\s*set\s*\(\s*SILKIT_VERSION_{}\s*([0-9]+)\s*\)\s*$"
    parts = []
    for component in ("MAJOR", "MINOR", "PATCH"):
        match = re.search(pattern.format(component), text, re.MULTILINE)
        if not match:
            sys.exit(f"no SILKIT_VERSION_{component} in the sil-kit sources")
        parts.append(match.group(1))
    return tuple(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg-dir", type=Path, required=True)
    ap.add_argument("--silkit-dir", type=Path, required=True)
    ap.add_argument("--expected-version", default="", help="major.minor.patch, empty to skip")
    args = ap.parse_args()

    major, minor, patch, suffix = deb_version(args.pkg_dir)
    deb = (major, minor, patch)
    checks = {
        "rpm/libsilkit5.spec": rpm_version(args.pkg_dir),
        "sil-kit sources": silkit_version(args.silkit_dir),
    }
    if args.expected_version:
        checks["expected_version"] = tuple(args.expected_version.split("-")[0].split("."))

    errors = [
        f"{name} has {'.'.join(version)}, debian/changelog has {'.'.join(deb)}"
        for name, version in checks.items()
        if version != deb
    ]
    if errors:
        sys.exit("version mismatch (is the changelog PR merged?):\n  " + "\n  ".join(errors))

    print(f"major={major}")
    print(f"minor={minor}")
    print(f"patch={patch}")
    print(f"suffix={suffix}")
    print(f"version={major}.{minor}.{patch}")


if __name__ == "__main__":
    main()
