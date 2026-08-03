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
import re
import sys
from datetime import datetime, timezone

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def timestamp_key(value):
    text = str(value or '').strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    try:
        parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp() * 1000)
    except ValueError:
        return None


def snapshot_is_newer(current_value, candidate_value):
    current_key = timestamp_key(current_value)
    candidate_key = timestamp_key(candidate_value)

    if candidate_key is None:
        return False
    if current_key is None:
        return True
    return candidate_key > current_key


def merge_unique_files(existing_files, incoming_files):
    by_key = {(item.get('filename'), item.get('type')): idx for idx, item in enumerate(existing_files)}
    for item in incoming_files:
        key = (item.get('filename'), item.get('type'))
        idx = by_key.get(key)
        if idx is None:
            existing_files.append(item)
            by_key[key] = len(existing_files) - 1
            continue
        existing = existing_files[idx]
        existing_hash = existing.get('backup_hash', '')
        incoming_hash = item.get('backup_hash', '')
        if (not existing_hash) and incoming_hash:
            existing_files[idx] = item
        elif existing_hash and incoming_hash and existing_hash != incoming_hash:
            print(
                f"WARN: Conflicting backup hashes for '{item.get('filename')}' "
                f"(type={item.get('type')}); marking as ambiguous.",
                file=sys.stderr,
            )
            existing_files[idx] = dict(existing, backup_hash='', hash_conflict=True)


def load_sums(path):
    sums = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                sha, fpath = parts
                sha = sha.strip().lower()
                if SHA256_RE.match(sha):
                    sums[fpath.lstrip('./')] = sha
    return sums


def load_csvs(paths):
    apps = {}
    for path in paths:
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            required_cols = {'ITEM_DATA', 'FILE_LIST', 'TIMESTAMP'}
            missing = required_cols - set(fieldnames)
            if missing:
                print(
                    f"WARN: Skipping {path} — missing required columns: {sorted(missing)}",
                    file=sys.stderr,
                )
                continue
            for index, row in enumerate(reader, start=2):
                item_data_raw = row.get('ITEM_DATA') or '{}'
                try:
                    meta = json.loads(item_data_raw)
                except json.JSONDecodeError as exc:
                    print(
                        f"WARN: Skipping malformed ITEM_DATA in {path}:{index}: {exc}",
                        file=sys.stderr,
                    )
                    continue
                if not isinstance(meta, dict):
                    print(
                        f"WARN: Skipping non-object ITEM_DATA in {path}:{index}",
                        file=sys.stderr,
                    )
                    continue
                pkg_raw = meta.get('package_name', '')
                if not isinstance(pkg_raw, str):
                    print(
                        f"WARN: Skipping non-string package_name in {path}:{index}",
                        file=sys.stderr,
                    )
                    continue
                pkg = pkg_raw.strip()
                if not pkg:
                    continue

                file_list_raw = row.get('FILE_LIST') or '[]'
                try:
                    file_list = json.loads(file_list_raw)
                except json.JSONDecodeError as exc:
                    print(
                        f"WARN: Skipping malformed FILE_LIST in {path}:{index}: {exc}",
                        file=sys.stderr,
                    )
                    continue
                if not isinstance(file_list, list):
                    print(
                        f"WARN: Skipping non-list FILE_LIST in {path}:{index}",
                        file=sys.stderr,
                    )
                    continue

                parsed_files = []
                malformed_apk_count = 0
                for item in file_list:
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get('type')
                    if item_type not in ('apk', 'apks'):
                        continue
                    item_path = item.get('path')
                    if not isinstance(item_path, str) or not item_path.strip():
                        print(
                            f"WARN: Skipping FILE_LIST entry without path in {path}:{index}",
                            file=sys.stderr,
                        )
                        malformed_apk_count += 1
                        continue
                    raw_hash = item.get('hash', '')
                    backup_hash = '' if raw_hash is None else str(raw_hash).strip().lower()
                    if backup_hash and not SHA256_RE.match(backup_hash):
                        print(
                            f"WARN: FILE_LIST entry has invalid hash in {path}:{index}; keeping as unverified",
                            file=sys.stderr,
                        )
                        backup_hash = ''
                    parsed_files.append(
                        {
                            'filename': os.path.basename(item_path),
                            'backup_hash': backup_hash,
                            'size': item.get('size', 0),
                            'type': item_type,
                        }
                    )

                if pkg not in apps:
                    ts_init = row.get('TIMESTAMP', '')
                    ts_init_key = timestamp_key(ts_init)
                    if ts_init_key is None and ts_init:
                        print(
                            f"WARN: Skipping row with invalid TIMESTAMP for new package {pkg} in {path}:{index}",
                            file=sys.stderr,
                        )
                        continue
                    apps[pkg] = {
                        'package_name': pkg,
                        'app_name': meta.get('app_name', ''),
                        'version_code': meta.get('version_code'),
                        'is_aab': meta.get('is_aab', True),
                        'backup_timestamp': ts_init,
                        'backup_files': [],
                        'has_malformed_apk_entries': False,
                    }

                app = apps[pkg]
                ts = row.get('TIMESTAMP', '')
                ts_key = timestamp_key(ts)
                if snapshot_is_newer(app.get('backup_timestamp', ''), ts):
                    # Keep package-level metadata aligned with the latest snapshot
                    # when the same package appears across multiple manifests.
                    app['app_name'] = meta.get('app_name', app.get('app_name', ''))
                    app['version_code'] = meta.get('version_code')
                    app['is_aab'] = meta.get('is_aab', app.get('is_aab', True))
                    app['backup_timestamp'] = ts
                    app['backup_files'] = list(parsed_files)
                    app['has_malformed_apk_entries'] = malformed_apk_count > 0
                elif ts_key is not None and ts_key == timestamp_key(app.get('backup_timestamp', '')):
                    merge_unique_files(app['backup_files'], parsed_files)
                    if malformed_apk_count > 0:
                        app['has_malformed_apk_entries'] = True
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

        # Section ends when the only non-empty cell is the first (either a
        # genuine 1-cell row or a row with trailing empty columns added by
        # Galaxy Store exports).
        if row[0].strip() and all(not c.strip() for c in row[1:]):
            break

        content_idx = header_idx.get('content id', -1)
        content_id = row[content_idx].strip() if content_idx >= 0 and content_idx < len(row) else ''
        model = (
            row[header_idx.get('device model id', -1)].strip()
            if 'device model id' in header_idx and header_idx.get('device model id', -1) < len(row)
            else ''
        )
        version = (
            row[header_idx.get('version of the last downloaded app', -1)].strip()
            if 'version of the last downloaded app' in header_idx and header_idx.get('version of the last downloaded app', -1) < len(row)
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
    epoch_str = os.environ.get('SOURCE_DATE_EPOCH', '')
    if epoch_str:
        try:
            generated_at = datetime.fromtimestamp(int(epoch_str), tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            generated_at = datetime.now(timezone.utc).isoformat()
    else:
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
                'hash_match': (bf['backup_hash'] == pulled_hash) if (bf['backup_hash'] and pulled_hash) else None,
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
            'backup_timestamp_ms': timestamp_key(info['backup_timestamp']),
            'pulled_from_device': pulled_device,
            'account_device_models': account_device_models,
            'galaxy_store': galaxy_store_evidence,
            'artifacts': pulled,
            'all_hashes_verified': (
                not info.get('has_malformed_apk_entries', False)
                and bool(pulled)
                and all(a['hash_match'] is True for a in pulled)
            ),
        })
    return {
        'generated_at': generated_at,
        'metadata': {
            'smartthings_account_devices': smartthings_devices,
            'galaxy_store_download_history': galaxy_store_summary,
            'pulled_from_device': pulled_device,
        },
        'packages': sorted(records, key=lambda r: r['package_name']),
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', nargs='+', required=True)
    p.add_argument('--sums', required=True)
    p.add_argument('--out', default='apks/provenance.json')
    p.add_argument('--galaxy-store-csv', default='')
    p.add_argument('--smartthings-csv', default='')
    p.add_argument('--device-serial', default=os.environ.get('DEVICE_SERIAL', ''))
    p.add_argument('--device-model', default=os.environ.get('DEVICE_MODEL', ''))
    args = p.parse_args()

    # Precondition: every --csv path and --sums must exist before reading.
    missing = [f for f in args.csv if not os.path.isfile(f)]
    if missing:
        for f in missing:
            print(f"ERROR: CSV file not found: {f}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.sums):
        print(f"ERROR: sums file not found: {args.sums}", file=sys.stderr)
        sys.exit(1)
    if args.galaxy_store_csv and not os.path.isfile(args.galaxy_store_csv):
        print(f"ERROR: --galaxy-store-csv not found: {args.galaxy_store_csv}", file=sys.stderr)
        sys.exit(1)
    if args.smartthings_csv and not os.path.isfile(args.smartthings_csv):
        print(f"ERROR: --smartthings-csv not found: {args.smartthings_csv}", file=sys.stderr)
        sys.exit(1)

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

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    tmp_out = args.out + '.tmp'
    try:
        with open(tmp_out, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, sort_keys=True)
        os.replace(tmp_out, args.out)
    except Exception:
        try:
            os.unlink(tmp_out)
        except OSError:
            pass
        raise
    print(f"Written {len(result['packages'])} package records to {args.out}")

if __name__ == '__main__':
    main()
