#! /bin/env python3
#
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
# Run with: python3 -m unittest discover -s tests -p "test_changelog*.py"
import sys
import unittest

from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from changelog_converter import parse_changelog  # noqa: E402

# Shaped like sil-kit docs/changelog/versions/5.0.8.md
SAMPLE = """# [5.0.8] - 2026-10-13

## Note on the SIL Kit MSI installer

Up to and including SIL Kit 5.0.7, the MSI installed per-user.

### What this means when you upgrade

- The 5.0.8 MSI can't detect an earlier per-user installation.
- Upgrading still works. The new installer:
  - disables the previous service, and
  - updates the CMake lookup.

| | Up to 5.0.7 | From 5.0.8 |
|---|---|---|

## Added

- Add Integration Test for Timestamp Behavior
- The documentation now lists every third party dependency found in the source tree with its
  version and license on the Licenses page, followed by the full license text of each component
  that ships one.

## Fixed

- The SIL Kit Registry could hang on shutdown.

# [5.0.7] - 2026-09-01

## Fixed

- Older entry
"""


class ParseChangelogTest(unittest.TestCase):

    def test_version_and_date(self):
        changelog = parse_changelog(SAMPLE.splitlines(True))
        self.assertEqual(changelog.version.pretty(), "5.0.8")
        self.assertEqual(changelog.cdate, date(2026, 10, 13))

    def test_only_change_sections(self):
        changes = parse_changelog(SAMPLE.splitlines(True)).changes
        self.assertEqual(changes, [
            "Add Integration Test for Timestamp Behavior",
            "The documentation now lists every third party dependency found in the source tree with its "
            "version and license on the Licenses page, followed by the full license text of each component "
            "that ships one.",
            "The SIL Kit Registry could hang on shutdown.",
        ])

    def test_header_is_not_appended(self):
        for change in parse_changelog(SAMPLE.splitlines(True)).changes:
            self.assertNotIn("#", change)

    def test_unreleased(self):
        changelog = parse_changelog(["# [5.0.9] - UNRELEASED\n", "\n", "## Added\n", "\n", "- New\n"],
                                    today=date(2026, 10, 27))
        self.assertEqual(changelog.cdate, date(2026, 10, 27))
        self.assertEqual(changelog.changes, ["New"])


if __name__ == "__main__":
    unittest.main()
