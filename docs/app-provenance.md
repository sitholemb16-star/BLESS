# App Provenance Pipeline

This repository tracks APK provenance from Samsung backup metadata to locally pulled APK binaries.

## 1) Pull APKs from the donor device

```bash
./scripts/pull-apks --serial <DONOR_DEVICE_SERIAL>
```

This pulls `base.apk` and split APKs into `apks/<package>/`.

## 2) Regenerate local hash manifest

```bash
./scripts/hash-apks
```

Output: `apks/SHA256SUMS.txt`

## 3) Verify against CSV `FILE_LIST[*].hash`

```bash
python3 tools/app_inventory/verify_hashes_against_csv.py \
  --csv apks/manifests/APP_*.csv \
  --sums apks/SHA256SUMS.txt
```

Notes:

- Hash mismatches are expected when apps changed between backup time and pull time.
- Use `--fail-on-mismatch` only when you need strict parity.

## 4) Build enriched provenance JSON

```bash
python3 tools/app_inventory/merge_csv_with_hashes.py \
  --csv apks/manifests/APP_*.csv \
  --sums apks/SHA256SUMS.txt \
  --galaxy-store-csv "<PATH_TO_GALAXY_STORE_EXPORT_CSV>" \
  --smartthings-csv "<PATH_TO_SMARTTHINGS_EXPORT_CSV>" \
  --device-serial <DONOR_DEVICE_SERIAL> \
  --device-model <DONOR_DEVICE_MODEL> \
  --out apks/provenance.json
```

### Provenance fields added per package

- `pulled_from_device`: donor serial/model used for APK extraction.
- `account_device_models`: device models observed in SmartThings account registry.
- `galaxy_store`: account-level Galaxy Store download evidence.

`downloaded_via_galaxy_store` is currently `null` because the Samsung export provides **content IDs** but no package-name mapping.

## 5) S25 emulator storage alignment

The AVD is created in external storage:

- `ANDROID_AVD_HOME=<EXTERNAL_AVD_HOME>`
- AVD name: `Galaxy-S25-128GB`
- Data partition: `128G` (sparse virtual disk)
