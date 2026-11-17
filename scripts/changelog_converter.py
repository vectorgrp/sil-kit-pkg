#! /bin/env python3
#
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
"""Add the newest entry of the SIL Kit changelog (docs/changelog/versions/latest.md)
to debian/changelog and rpm/libsilkit5.spec.

Moved here from sil-kit-delivery (scripts/changelog_converter.py). Only the bullets of the
Keep a Changelog sections (Added, Changed, Deprecated, Removed, Fixed, Security) are taken
over; other sections such as notes and tables are skipped, and section headers no longer
end up in the previous entry.
"""
import argparse
import os
import re
import shutil
import sys
import textwrap

from datetime import date, datetime
from pathlib import Path

CHANGE_SECTIONS = {"added", "changed", "deprecated", "removed", "fixed", "security"}


def log(fmt, *args):
    print(fmt.format(*args))


def die(status, fmt, *args):
    log("ERROR: " + fmt, *args)
    sys.exit(status)


class SilKitVersion:
    def __init__(self, major: int, minor: int, patch: int, suffix: str = ""):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.suffix = suffix

    def pretty_for_git(self):
        version_str = f"{self.major}.{self.minor}.{self.patch}"
        if self.suffix and self.suffix != "":
            version_str += f"-{self.suffix}"
        return version_str

    def pretty(self):
        version_str = f"{self.major}.{self.minor}.{self.patch}"
        if self.suffix and self.suffix != "":
            version_str += f"~{self.suffix}"
        return version_str


class Changes:
    def __init__(self, change_date: date, version: SilKitVersion):
        self.changes = []
        self.cdate = change_date
        self.version = version


def parse_changelog(lines, today: date = None) -> Changes:
    """Parse the first (newest) version of a SIL Kit changelog in markdown."""

    changelog = None
    section = None
    in_entry = False

    for line in lines:
        line = line.rstrip("\n")

        if line.startswith("# "):
            if changelog is not None:
                log("Older version, stopping the processing")
                break

            ver_reg = r"^#\s\[([0-9]+)\.([0-9]+)\.([0-9]+)\]\s+\-\s+([0-9]+\-[0-9]+\-[0-9]+|UNRELEASED)"
            reg = re.match(ver_reg, line)
            if reg is None:
                die(64, "Malformed changelog header: {}", line)

            date_string = reg.group(4).strip()
            if date_string == "UNRELEASED":
                release_date = today or date.today()
            else:
                release_date = date(int(date_string[0:4]), int(date_string[5:7]), int(date_string[8:10]))

            changelog = Changes(release_date, SilKitVersion(major=reg.group(1), minor=reg.group(2), patch=reg.group(3)))
            log("Found version {} from {}", changelog.version.pretty_for_git(), release_date)

        elif line.startswith("#"):
            # "## Fixed", "### Details" ...: a header always ends the current entry
            in_entry = False
            if line.startswith("## "):
                section = line[3:].strip().lower()

        elif line.startswith("* ") or line.startswith("- "):
            if changelog is None:
                die(64, "Malformed changelog, no changelog header found!")
            in_entry = section in CHANGE_SECTIONS
            if in_entry:
                changelog.changes.append(line[2:].strip())

        elif in_entry and line[:1].isspace() and line.strip():
            # indented continuation line (or nested bullet) of the current entry
            changelog.changes[-1] += " " + line.strip()

        else:
            # blank lines, paragraphs and tables
            in_entry = False

    if changelog is None:
        die(64, "Malformed changelog, no changelog header found!")
    return changelog


def write_deb_log(changelog: Changes, args):

    header = f"libsilkit ({changelog.version.pretty()}-1ubuntu1) stable; urgency=medium"
    footer = f"\n -- {args.name} <{args.mail}>  {changelog.cdate.strftime('%a, %d %b %Y')} {datetime.now().astimezone().strftime('%H:%M:%S %z')}"

    entry = header + "\n"
    for change in changelog.changes:
        entry += "  * " + "\n".join(textwrap.wrap(change, width=76, subsequent_indent="    ")) + "\n"
    entry += footer + "\n\n"

    print(entry)
    if args.dryrun:
        print("Exiting due to dryrun!\n")
        return

    changelog_path = args.package_dir / "debian/changelog"
    with open(changelog_path, "r") as f:
        old = f.read()
    with open(changelog_path, "w") as f:
        f.write(entry + old)


def write_rpm_log(changelog: Changes, args):

    header = f"* {changelog.cdate.strftime('%a %b %d %Y')} {args.name} <{args.mail}> - {changelog.version.pretty()}"

    entry = header + "\n"
    for change in changelog.changes:
        entry += "- " + "\n".join(textwrap.wrap(change, width=76, subsequent_indent="  ")) + "\n"

    print(entry)
    if args.dryrun:
        print("Exiting due to dryrun!\n")
        return

    spec_path = args.package_dir / "rpm/libsilkit5.spec"
    with open(spec_path, "r") as f:
        lines = f.readlines()

    with open(spec_path, "w") as f:
        f.write(f"%define version_major {changelog.version.major}\n")
        f.write(f"%define version_minor {changelog.version.minor}\n")
        f.write(f"%define version_patch {changelog.version.patch}\n")
        f.write("%define version_suffix %{nil}\n")

        for line in lines:
            if "define version" not in line:
                f.write(line)

            if "%changelog" in line:
                print("Writing new changelog entry!")
                f.write("\n" + entry)


def main():

    parser = argparse.ArgumentParser(prog="ChaparONE",
                                     description="Parse and create changelogs for SIL Kit releases")
    parser.add_argument("name", type=str)
    parser.add_argument("mail", type=str)
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--changelog", type=Path, default=Path("sil-kit/docs/changelog/versions/latest.md"),
                        help="SIL Kit changelog in markdown")
    parser.add_argument("--dryrun", action="store_true")
    args = parser.parse_args()

    with open(args.changelog, "rt", encoding="utf-8") as f:
        changelog = parse_changelog(f)

    if not changelog.changes:
        die(64, "{} has no entries for {}", args.changelog, changelog.version.pretty())

    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"silkit_version={changelog.version.pretty_for_git()}\n")

    print(f"Changelog Version: {changelog.version.pretty()}")

    write_deb_log(changelog, args)
    write_rpm_log(changelog, args)


if __name__ == "__main__":

    main()
