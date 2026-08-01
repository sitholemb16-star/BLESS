# App Provenance Pipeline

This repository tracks APK provenance from Samsung backup metadata to locally pulled APK binaries.

## 1) Pull APKs from the donor device (A04)

```bash
./scripts/pull-apks --serial R83WA0GJ03V
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
  --galaxy-store-csv "/Volumes/2027 Final Drafts/SamsungCloud/Samsung_2ND_SAM_unzipped/galaxyapps_gk000068459847_20260717_access/GalaxyStore_1048629395_20260717_access.csv" \
  --smartthings-csv "/Volumes/2027 Final Drafts/SamsungCloud/Samsung_2ND_SAM_unzipped/SmartThings_gk000068459851_20260716_access/SmartThings_Client.csv" \
  --device-serial R83WA0GJ03V \
  --device-model SM-A042F \
  --out apks/provenance.json
```

### Provenance fields added per package

- `pulled_from_device`: donor serial/model used for APK extraction.
- `account_device_models`: device models observed in SmartThings account registry.
- `galaxy_store`: account-level Galaxy Store download evidence.

`downloaded_via_galaxy_store` is currently `null` because the Samsung export provides **content IDs** but no package-name mapping.

## 5) S25 emulator storage alignment

The AVD is created in external storage:

- `ANDROID_AVD_HOME=/Volumes/VOLUME 1/2027 Final Drafts.sparsebundle/android-avd`
- AVD name: `Galaxy-S25-128GB`
- Data partition: `128G` (sparse virtual disk)
