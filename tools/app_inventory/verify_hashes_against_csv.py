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
import sys


def load_sums(path):
    sums = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            sha, rel_path = parts
            sums[rel_path.lstrip("./")] = sha
    return sums


def load_expected(csv_paths):
    expected = {}
    for path in csv_paths:
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    meta = json.loads(row.get("ITEM_DATA", "{}"))
                    pkg = meta.get("package_name")
                    if not pkg:
                        continue
                    file_list = json.loads(row.get("FILE_LIST", "[]"))
                    for item in file_list:
                        item_type = item.get("type")
                        if item_type not in ("apk", "apks"):
                            continue
                        rel = f"apks/{pkg}/{item['path'].split('/')[-1]}"
                        expected[rel] = {
                            "backup_hash": item.get("hash", ""),
                            "package_name": pkg,
                            "type": item_type,
                        }
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
    return expected


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

    sums = load_sums(args.sums)
    expected = load_expected(args.csv)

    matched = 0
    mismatched = 0
    missing_local = 0
    missing_backup = 0
    mismatch_rows = []

    for rel_path, exp in expected.items():
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

    if mismatch_rows:
        print("\nTop mismatches:")
        for pkg, rel, backup_hash, local_hash in mismatch_rows[:20]:
            print(f"  - {pkg}: {rel}")
            print(f"    backup={backup_hash}")
            print(f"    local ={local_hash}")

    if args.fail_on_mismatch and mismatched > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
