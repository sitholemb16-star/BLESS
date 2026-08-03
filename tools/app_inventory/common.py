import csv
import json
import re
import sys

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def normalized_apk_filename(path):
    return path.strip().replace("\\", "/").split("/")[-1]


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
            norm = rel_path.replace("\\", "/")
            if norm.startswith("./"):
                norm = norm[2:]
            if norm in sums:
                print(
                    f"WARN: Duplicate path in sums file (second entry ignored): {norm!r}",
                    file=sys.stderr,
                )
                invalid_local_rows += 1
                continue
            sums[norm] = sha
    return sums, invalid_local_rows


def iter_app_csv_rows(csv_paths):
    for path in csv_paths:
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, strict=True)
            fieldnames = reader.fieldnames or []
            missing = {"ITEM_DATA", "FILE_LIST", "TIMESTAMP"} - set(fieldnames)
            if missing:
                print(
                    f"WARN: Skipping {path} - missing required columns: {sorted(missing)}",
                    file=sys.stderr,
                )
                yield {"invalid": True, "skip": True}
                continue

            row_iter = iter(reader)
            index = 2
            while True:
                try:
                    row = next(row_iter)
                except StopIteration:
                    break
                except csv.Error as exc:
                    print(f"WARN: Malformed CSV row in {path}:{index}: {exc}", file=sys.stderr)
                    yield {"invalid": True, "skip": True}
                    index += 1
                    continue
                yield parse_app_csv_row(row, path, index)
                index += 1


def parse_app_csv_row(row, path, index):
    item_data_raw = row.get("ITEM_DATA") or "{}"
    try:
        meta = json.loads(item_data_raw)
    except json.JSONDecodeError as exc:
        print(
            f"WARN: Skipping malformed ITEM_DATA in {path}:{index}: {exc}",
            file=sys.stderr,
        )
        return {"invalid": True, "skip": True}
    if not isinstance(meta, dict):
        print(f"WARN: Skipping non-object ITEM_DATA in {path}:{index}", file=sys.stderr)
        return {"invalid": True, "skip": True}
    pkg_raw = meta.get("package_name", "")
    if not isinstance(pkg_raw, str):
        print(f"WARN: Skipping non-string package_name in {path}:{index}", file=sys.stderr)
        return {"invalid": True, "skip": True}
    pkg = pkg_raw.strip()
    if not pkg:
        return {"invalid": False, "skip": True}

    parsed_files, malformed_apk_count = parse_file_list(row, path, index)
    return {
        "invalid": malformed_apk_count > 0,
        "skip": False,
        "path": path,
        "index": index,
        "row": row,
        "meta": meta,
        "package_name": pkg,
        "parsed_files": parsed_files,
        "malformed_apk_count": malformed_apk_count,
    }


def parse_file_list(row, path, index):
    file_list_raw = row.get("FILE_LIST") or "[]"
    try:
        file_list = json.loads(file_list_raw)
    except json.JSONDecodeError as exc:
        print(f"WARN: malformed FILE_LIST in {path}:{index}: {exc}", file=sys.stderr)
        return [], 1
    if not isinstance(file_list, list):
        print(f"WARN: non-list FILE_LIST in {path}:{index}", file=sys.stderr)
        return [], 1

    parsed_files = []
    malformed_apk_count = 0
    for item in file_list:
        if not isinstance(item, dict):
            malformed_apk_count += 1
            print(f"WARN: non-object FILE_LIST entry in {path}:{index}", file=sys.stderr)
            continue
        item_type = item.get("type")
        if item_type not in ("apk", "apks"):
            continue
        item_path = item.get("path")
        if not isinstance(item_path, str) or not item_path.strip():
            print(f"WARN: FILE_LIST entry missing path in {path}:{index}", file=sys.stderr)
            malformed_apk_count += 1
            continue
        raw_hash = item.get("hash", "")
        if raw_hash is not None and not isinstance(raw_hash, str):
            print(f"WARN: FILE_LIST entry has non-string hash type in {path}:{index}", file=sys.stderr)
            malformed_apk_count += 1
            backup_hash = ""
        else:
            backup_hash = "" if raw_hash is None else raw_hash.strip().lower()
        if backup_hash and not SHA256_RE.match(backup_hash):
            print(
                f"WARN: FILE_LIST entry has invalid hash in {path}:{index}; keeping as unverified",
                file=sys.stderr,
            )
            backup_hash = ""
        parsed_files.append(
            {
                "filename": normalized_apk_filename(item_path),
                "backup_hash": backup_hash,
                "size": item.get("size", 0),
                "type": item_type,
            }
        )
    return parsed_files, malformed_apk_count
