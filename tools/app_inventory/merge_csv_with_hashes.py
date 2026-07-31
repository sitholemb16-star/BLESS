#!/usr/bin/env python3
"""
merge_csv_with_hashes.py
Joins Samsung Cloud backup CSV manifests with pulled APK sha256 hashes.
Produces a provenance JSON linking package / version / backup hash / pulled hash / timestamp.

Usage:
    python3 tools/app_inventory/merge_csv_with_hashes.py \
        --csv APP_1784239533045.csv APP_1784239532891.csv \
        --sums apks/SHA256SUMS.txt \
        --out apks/provenance.json
"""
import argparse, csv, hashlib, json, os, sys
from datetime import datetime, timezone

def load_sums(path):
    sums = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                sha, fpath = parts
                sums[fpath.lstrip('./')] = sha
    return sums

def load_csvs(paths):
    apps = {}
    for path in paths:
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                try:
                    meta = json.loads(row.get('ITEM_DATA', '{}'))
                    pkg = meta.get('package_name', '')
                    if not pkg:
                        continue
                    file_list = json.loads(row.get('FILE_LIST', '[]'))
                    apps[pkg] = {
                        'package_name': pkg,
                        'app_name': meta.get('app_name', ''),
                        'version_code': meta.get('version_code'),
                        'is_aab': meta.get('is_aab', True),
                        'backup_timestamp': row.get('TIMESTAMP', ''),
                        'backup_files': [
                            {
                                'filename': os.path.basename(f['path']),
                                'backup_hash': f.get('hash', ''),
                                'size': f.get('size', 0),
                                'type': f.get('type', ''),
                            }
                            for f in file_list if f.get('type') in ('apk', 'apks')
                        ]
                    }
                except Exception:
                    pass
    return apps

def merge(apps, sums):
    records = []
    generated_at = datetime.now(timezone.utc).isoformat()
    for pkg, info in sorted(apps.items()):
        pulled = []
        for bf in info['backup_files']:
            local_path = f"apks/{pkg}/{bf['filename']}"
            pulled_hash = sums.get(local_path, None)
            pulled.append({
                'filename': bf['filename'],
                'backup_hash_sha256': bf['backup_hash'],
                'pulled_hash_sha256': pulled_hash,
                'size_bytes': bf['size'],
                'type': bf['type'],
                'hash_match': bf['backup_hash'] == pulled_hash if pulled_hash else None,
            })
        records.append({
            'package_name': pkg,
            'app_name': info['app_name'],
            'version_code': info['version_code'],
            'is_aab': info['is_aab'],
            'backup_timestamp_ms': info['backup_timestamp'],
            'artifacts': pulled,
            'all_hashes_verified': all(
                a['hash_match'] is True for a in pulled
            ) if pulled else False,
        })
    return {'generated_at': generated_at, 'packages': records}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', nargs='+', required=True)
    p.add_argument('--sums', required=True)
    p.add_argument('--out', default='apks/provenance.json')
    args = p.parse_args()

    apps = load_csvs(args.csv)
    sums = load_sums(args.sums)
    result = merge(apps, sums)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Written {len(result['packages'])} package records to {args.out}")

if __name__ == '__main__':
    main()
