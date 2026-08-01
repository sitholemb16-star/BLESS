# BLESS

I am blessed to create and share creation.

## Overview
BLESS is a personal project focused on secure development workflows and authenticated API code practices.

## Getting Started

### Prerequisites
- Node.js 20+
- npm (or yarn)

### Install
```bash
npm ci
```

If using yarn:
```bash
yarn install --frozen-lockfile
```

## Development

### Lint
```bash
npm run lint
```

### Test
```bash
npm test
```

## Device APK Provenance Workflow

Pull APKs directly from the connected phone over ADB, then regenerate the integrity and provenance artifacts.

### Pull packages from the phone
```bash
./scripts/pull-apks --serial R83WA0GJ03V
```

The package list lives in `apks/packages.txt`. The script skips packages that are no longer installed on the device.

### Regenerate hashes
```bash
./scripts/hash-apks
```

### Build provenance JSON from Samsung backup manifests
```bash
python3 tools/app_inventory/merge_csv_with_hashes.py \
  --csv <APP_manifest_1.csv> <APP_manifest_2.csv> \
  --sums apks/SHA256SUMS.txt \
  --out apks/provenance.json
```

The resulting `apks/provenance.json` links backup metadata to pulled local APK hashes.

## Security Notes
- Never commit secrets, API keys, or tokens.
- Use environment variables or GitHub Secrets for sensitive values.
- Keep dependency installs lockfile-based (`package-lock.json` or `yarn.lock`).
- Use pinned GitHub Actions with full commit SHA.

## Contributing
This repository is maintained by the owner. Contributions should follow repository security and workflow policies.

## License
Add your preferred license (for example: MIT).
