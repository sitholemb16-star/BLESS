#!/usr/bin/env python3
"""
Verify locally pulled APK hashes against FILE_LIST[*].hash values in Samsung APP export CSVs.

This script compares:
  CSV FILE_LIST hash (backup-side) vs local apks/SHA256SUMS.txt (pull-side)

By default, mismatches are reported but do not fail the process because
apps can update between backup time and pull time.
"""
import argparse
import csv
import json
import re
import sys

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def load_sums(path):
    sums = {}
    invalid_local_rows = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                invalid_local_rows += 1
                continue
            sha, rel_path = parts
            sha = sha.strip().lower()
            if not SHA256_RE.match(sha):
                invalid_local_rows += 1
                continue
            sums[rel_path.lstrip("./")] = sha
    return sums, invalid_local_rows


def load_expected(csv_paths):
    expected = []
    invalid_rows = 0
    for path in csv_paths:
        with open(path, encoding="utf-8-sig") as f:
            for index, row in enumerate(csv.DictReader(f), start=2):
                try:
                    meta = json.loads(row.get("ITEM_DATA", "{}"))
                    if not isinstance(meta, dict):
                        invalid_rows += 1
                        print(
                            f"WARN: non-object ITEM_DATA in {path}:{index}",
                            file=sys.stderr,
                        )
                        continue
                    pkg = meta.get("package_name")
                    if not isinstance(pkg, str) or not pkg.strip():
                        invalid_rows += 1
                        print(
                            f"WARN: missing/invalid package_name in {path}:{index}",
                            file=sys.stderr,
                        )
                        continue
                    pkg = pkg.strip()
                    file_list = json.loads(row.get("FILE_LIST", "[]"))
                    if not isinstance(file_list, list):
                        invalid_rows += 1
                        print(
                            f"WARN: non-list FILE_LIST in {path}:{index}",
                            file=sys.stderr,
                        )
                        continue
                    for item in file_list:
                        if not isinstance(item, dict):
                            invalid_rows += 1
                            print(
                                f"WARN: non-object FILE_LIST entry in {path}:{index}",
                                file=sys.stderr,
                            )
                            continue
                        item_type = item.get("type")
                        if item_type not in ("apk", "apks"):
                            continue
                        item_path = item.get("path")
                        if not isinstance(item_path, str) or not item_path.strip():
                            invalid_rows += 1
                            print(
                                f"WARN: FILE_LIST entry missing path in {path}:{index}",
                                file=sys.stderr,
                            )
                            continue
                        item_path = item_path.strip()
                        raw_hash = item.get("hash", "")
                        backup_hash = "" if raw_hash is None else str(raw_hash).strip()
                        if backup_hash and not SHA256_RE.match(backup_hash):
                            invalid_rows += 1
                            print(
                                f"WARN: invalid FILE_LIST hash in {path}:{index}",
                                file=sys.stderr,
                            )
                            continue
                        rel = f"apks/{pkg}/{item_path.split('/')[-1]}"
                        expected.append(
                            {
                                "rel_path": rel,
                                "backup_hash": backup_hash.lower(),
                                "package_name": pkg,
                                "type": item_type,
                            }
                        )
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    invalid_rows += 1
                    print(
                        f"WARN: malformed row in {path}:{index}",
                        file=sys.stderr,
                    )
                    continue
    return expected, invalid_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", nargs="+", required=True, help="APP_*.csv files")
    ap.add_argument("--sums", required=True, help="apks/SHA256SUMS.txt")
    ap.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit non-zero if any hash mismatch is found",
    )
    args = ap.parse_args()

    sums, invalid_local_rows = load_sums(args.sums)
    expected, invalid_rows = load_expected(args.csv)
    invalid_rows += invalid_local_rows

    matched = 0
    mismatched = 0
    missing_local = 0
    missing_backup = 0
    mismatch_rows = []

    expected_paths = {exp["rel_path"] for exp in expected}
    local_only = sorted(set(sums.keys()) - expected_paths)

    for exp in expected:
        rel_path = exp["rel_path"]
        backup_hash = exp["backup_hash"]
        local_hash = sums.get(rel_path)
        if local_hash is None:
            missing_local += 1
            continue
        if not backup_hash:
            missing_backup += 1
            continue
        if local_hash == backup_hash:
            matched += 1
        else:
            mismatched += 1
            mismatch_rows.append((exp["package_name"], rel_path, backup_hash, local_hash))

    print("CSV FILE_LIST.hash verification summary")
    print(f"  expected_artifacts: {len(expected)}")
    print(f"  local_artifacts:    {len(sums)}")
    print(f"  matched:            {matched}")
    print(f"  mismatched:         {mismatched}")
    print(f"  missing_local:      {missing_local}")
    print(f"  missing_backup:     {missing_backup}")
    print(f"  invalid_rows:       {invalid_rows}")
    print(f"  local_only:         {len(local_only)}")

    if mismatch_rows:
        print("\nTop mismatches:")
        for pkg, rel, backup_hash, local_hash in mismatch_rows[:20]:
            print(f"  - {pkg}: {rel}")
            print(f"    backup={backup_hash}")
            print(f"    local ={local_hash}")

    if local_only:
        print("\nLocal-only APKs (present in SHA256SUMS.txt but absent from any CSV FILE_LIST):")
        for rel in local_only[:20]:
            print(f"  - {rel}")
        if len(local_only) > 20:
            print(f"  ... and {len(local_only) - 20} more")

    if args.fail_on_mismatch and (
        mismatched > 0 or missing_local > 0 or missing_backup > 0 or invalid_rows > 0
        or len(local_only) > 0
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
