#!/usr/bin/env python3
"""
merge_csv_with_hashes.py
Joins Samsung Cloud backup CSV manifests with pulled APK sha256 hashes.
Produces a provenance JSON linking package/version/hash details and account/device evidence.
"""
import argparse
import csv
import json
import os
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
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
    return apps


def parse_smartthings_devices(path):
    if not path:
        return []

    devices = []
    with open(path, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            model = (row.get('MODEL NUMBER') or '').strip()
            if not model:
                continue
            devices.append(
                {
                    'device_id': (row.get('DEVICE ID') or '').strip(),
                    'model_number': model,
                    'manufacturer': (row.get('MANUFACTURER NAME') or '').strip(),
                    'platform_os': (row.get('PLATFORM OPERATING SYSTEM') or '').strip(),
                    'platform_version': str(row.get('PLATFORM VERSION') or '').strip(),
                    'first_seen': (row.get('CREATE TIME') or '').strip(),
                    'last_seen': (row.get('UPDATE TIME') or '').strip(),
                }
            )

    # De-duplicate by device_id/model tuple while preserving order
    dedup = []
    seen = set()
    for d in devices:
        key = (d['device_id'], d['model_number'])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(d)
    return dedup


def parse_galaxy_store_download_history(path):
    """
    Parse the GDPR Galaxy Store export section:
      'Download history by user and device'
    This section has content IDs + device model IDs but no package names.
    """
    result = {
        'record_count': 0,
        'device_models': [],
        'content_ids': [],
        'has_package_mapping': False,
    }
    if not path:
        return result

    records = []
    content_ids = set()
    device_models = set()

    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))

    in_section = False
    header = None
    header_idx = {}
    for row in rows:
        if not row:
            continue
        first = (row[0] or '').strip()
        if first == 'Download history by user and device':
            in_section = True
            header = None
            header_idx = {}
            continue
        if not in_section:
            continue
        if header is None:
            header = [c.strip() for c in row]
            header_idx = {name: idx for idx, name in enumerate(header)}
            continue

        # Section ends at the next labeled header block.
        if len(row) == 1 and row[0].strip():
            break

        content_id = row[header_idx.get('content id', -1)].strip() if 'content id' in header_idx else ''
        model = (
            row[header_idx.get('device model id', -1)].strip()
            if 'device model id' in header_idx
            else ''
        )
        version = (
            row[header_idx.get('version of the last downloaded app', -1)].strip()
            if 'version of the last downloaded app' in header_idx
            else ''
        )
        if not content_id and not model:
            continue
        records.append(
            {
                'content_id': content_id,
                'device_model_id': model,
                'last_downloaded_version': version,
            }
        )
        if content_id:
            content_ids.add(content_id)
        if model:
            device_models.add(model)

    result['record_count'] = len(records)
    result['device_models'] = sorted(device_models)
    result['content_ids'] = sorted(content_ids)
    return result


def merge(apps, sums, *, smartthings_devices, galaxy_store_summary, pulled_device):
    records = []
    generated_at = datetime.now(timezone.utc).isoformat()
    account_device_models = sorted(
        {
            d['model_number']
            for d in smartthings_devices
            if d.get('model_number')
        }
    )

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

        # Package-level Galaxy Store linkage is unknown with this export shape
        # because it provides content IDs, not package names.
        galaxy_store_evidence = {
            'account_download_history_present': galaxy_store_summary['record_count'] > 0,
            'account_download_device_models': galaxy_store_summary['device_models'],
            'content_id_linkage_available': galaxy_store_summary['has_package_mapping'],
            'downloaded_via_galaxy_store': None,
            'status': 'unknown_no_package_to_content_id_mapping_in_export',
        }

        records.append({
            'package_name': pkg,
            'app_name': info['app_name'],
            'version_code': info['version_code'],
            'is_aab': info['is_aab'],
            'backup_timestamp_ms': info['backup_timestamp'],
            'pulled_from_device': pulled_device,
            'account_device_models': account_device_models,
            'galaxy_store': galaxy_store_evidence,
            'artifacts': pulled,
            'all_hashes_verified': all(
                a['hash_match'] is True for a in pulled
            ) if pulled else False,
        })
    return {
        'generated_at': generated_at,
        'metadata': {
            'smartthings_account_devices': smartthings_devices,
            'galaxy_store_download_history': galaxy_store_summary,
            'pulled_from_device': pulled_device,
        },
        'packages': records,
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', nargs='+', required=True)
    p.add_argument('--sums', required=True)
    p.add_argument('--out', default='apks/provenance.json')
    p.add_argument('--galaxy-store-csv', default='')
    p.add_argument('--smartthings-csv', default='')
    p.add_argument('--device-serial', default='')
    p.add_argument('--device-model', default='')
    args = p.parse_args()

    apps = load_csvs(args.csv)
    sums = load_sums(args.sums)
    smartthings_devices = parse_smartthings_devices(args.smartthings_csv)
    galaxy_store_summary = parse_galaxy_store_download_history(args.galaxy_store_csv)
    pulled_device = {
        'serial': args.device_serial,
        'model': args.device_model,
    }
    result = merge(
        apps,
        sums,
        smartthings_devices=smartthings_devices,
        galaxy_store_summary=galaxy_store_summary,
        pulled_device=pulled_device,
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Written {len(result['packages'])} package records to {args.out}")

if __name__ == '__main__':
    main()
