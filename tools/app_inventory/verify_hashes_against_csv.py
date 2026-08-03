#!/usr/bin/env python3
"""
Verify locally pulled APK hashes against FILE_LIST[*].hash values in Samsung APP export CSVs.

This script compares:
  CSV FILE_LIST hash (backup-side) vs local apks/SHA256SUMS.txt (pull-side)

By default, mismatches are reported but do not fail the process because
apps can update between backup time and pull time.
"""
import argparse
import os
import sys

from common import iter_app_csv_rows, load_sums


def load_expected(csv_paths):
    expected = []
    invalid_rows = 0
    for row in iter_app_csv_rows(csv_paths):
        if row.get("invalid"):
            invalid_rows += 1
        if row.get("skip"):
            continue
        pkg = row["package_name"]
        for item in row["parsed_files"]:
            expected.append(
                {
                    "rel_path": f"apks/{pkg}/{item['filename']}",
                    "backup_hash": item["backup_hash"],
                    "package_name": pkg,
                    "type": item["type"],
                }
            )
    return expected, invalid_rows



def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", nargs="+", required=True, help="APP_*.csv files")
    ap.add_argument("--sums", required=True, help="apks/SHA256SUMS.txt")
    ap.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help=(
            "Exit non-zero (code 2) when any of the following are detected: "
            "hash mismatches, APKs missing locally, APKs without a backup hash, "
            "malformed CSV/sums rows, or extra local APKs not referenced by any CSV. "
            "This is a fail-closed gate: any deviation from a fully consistent state "
            "causes a non-zero exit."
        ),
    )
    args = ap.parse_args()

    # Precondition: every --csv path and --sums must exist before reading.
    missing = [f for f in args.csv if not os.path.isfile(f)]
    if missing:
        for f in missing:
            print(f"ERROR: CSV file not found: {f}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.sums):
        print(f"ERROR: sums file not found: {args.sums}", file=sys.stderr)
        sys.exit(1)

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
