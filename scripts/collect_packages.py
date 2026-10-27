#! /bin/env python3
#
# SPDX-FileCopyrightText: 2026 Vector Informatik GmbH
#
# SPDX-License-Identifier: MIT
#
"""Helpers for package-silkit.yml.

  select   copy the files of one target that match its asset globs into a directory
           and write <id>.target.json next to them
  manifest merge the per-target directories into one and write pkg-manifest.json and SHA256
"""
import argparse
import hashlib
import json
import shutil
import sys

from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select(args):
    target = json.loads(args.target)
    args.dest.mkdir(parents=True, exist_ok=True)

    files = []
    for pattern in target["assets"]:
        matches = sorted(p for p in args.source.glob(pattern) if p.is_file())
        if not matches:
            sys.exit(f"{target['id']}: no file matches {pattern} in {args.source}")
        for match in matches:
            if match.name not in files:
                shutil.copy2(match, args.dest / match.name)
                files.append(match.name)

    info = {
        "id": target["id"],
        "release": target["release"],
        "image": target["image"],
        "image_digest": args.image_digest,
        "files": files,
    }
    with open(args.dest / f"{target['id']}.target.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    print(json.dumps(info, indent=2))


def manifest(args):
    args.dest.mkdir(parents=True, exist_ok=True)

    targets = []
    files = []
    for target_json in sorted(args.source.glob("*/*.target.json")):
        with open(target_json, "r", encoding="utf-8") as f:
            target = json.load(f)
        for name in target["files"]:
            path = target_json.parent / name
            if (args.dest / name).exists():
                sys.exit(f"{name} is produced by more than one target")
            shutil.copy2(path, args.dest / name)
            files.append({
                "name": name,
                "target": target["id"],
                "release": target["release"],
                "sha256": sha256(path),
                "size": path.stat().st_size,
            })
        targets.append({k: target[k] for k in ("id", "release", "image", "image_digest")})

    if not files:
        sys.exit("no packages found")

    pkg_manifest = {
        "version": args.version,
        "silkit_ref": args.silkit_ref,
        "silkit_sha": args.silkit_sha,
        "silkit_submodules": json.loads(args.silkit_submodules),
        "pkg_sha": args.pkg_sha,
        "source_date_epoch": int(args.source_date_epoch),
        "run_url": args.run_url,
        "targets": targets,
        "files": files,
    }
    with open(args.dest / "pkg-manifest.json", "w", encoding="utf-8") as f:
        json.dump(pkg_manifest, f, indent=2)
        f.write("\n")
    with open(args.dest / "SHA256", "w", encoding="utf-8") as f:
        for entry in files:
            f.write(f"{entry['sha256']}  {entry['name']}\n")
    print(json.dumps(pkg_manifest, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    s = sub.add_parser("select")
    s.add_argument("--target", required=True, help="target object from release/packages.json as JSON")
    s.add_argument("--source", type=Path, required=True)
    s.add_argument("--dest", type=Path, required=True)
    s.add_argument("--image-digest", default="")
    s.set_defaults(func=select)

    m = sub.add_parser("manifest")
    m.add_argument("--source", type=Path, required=True, help="directory with one subdirectory per target")
    m.add_argument("--dest", type=Path, required=True)
    m.add_argument("--version", required=True)
    m.add_argument("--silkit-ref", required=True)
    m.add_argument("--silkit-sha", required=True)
    m.add_argument("--silkit-submodules", default="{}", help="JSON object path -> sha")
    m.add_argument("--pkg-sha", required=True)
    m.add_argument("--source-date-epoch", required=True)
    m.add_argument("--run-url", required=True)
    m.set_defaults(func=manifest)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
