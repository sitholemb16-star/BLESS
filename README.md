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
  --csv <APP_manifest_1.csv> <APP_manifest_2.csv> <APP_manifest_3.csv> \
  --sums apks/SHA256SUMS.txt \
  --out apks/provenance.json
```

The resulting `apks/provenance.json` links backup metadata to pulled local APK hashes.  
It is treated as generated local evidence and is git-ignored by default.

### Verify against CSV FILE_LIST hashes
```bash
python3 tools/app_inventory/verify_hashes_against_csv.py \
  --csv apks/manifests/APP_*.csv \
  --sums apks/SHA256SUMS.txt
```

## Galaxy S25 Emulator Setup (External Storage)

Use the external sparsebundle-backed path for AVD storage:

- AVD home: `/Volumes/VOLUME 1/2027 Final Drafts.sparsebundle/android-avd`
- AVD name: `Galaxy-S25-128GB`

Create/update the AVD:
```bash
./scripts/setup-s25-avd
```

Launch it:
```bash
./scripts/launch-s25
```

Install pulled APK set into the running emulator:
```bash
./scripts/install-apks-to-emulator --serial emulator-5554
```

## Security Notes
- Never commit secrets, API keys, or tokens.
- Use environment variables or GitHub Secrets for sensitive values.
- Keep dependency installs lockfile-based (`package-lock.json` or `yarn.lock`).
- Use pinned GitHub Actions with full commit SHA.

## Signed Commit Enforcement (main branch)

`main` is protected by an active ruleset that requires:
- signed commits
- pull request approval (1)
- required checks: `API Tests`, `Auto Copilot Review`

### 1) Check local signing configuration
```bash
git config --get commit.gpgsign
git config --get user.signingkey
git config --get gpg.format
```

Expected:
- `commit.gpgsign=true`
- `user.signingkey` set
- `gpg.format=ssh` (SSH signing) or `openpgp` (GPG signing)

### 2) Verify `git commit -S` works locally
```bash
git checkout -b test-protection
echo "test enforcement" > test.txt
git add test.txt
git commit -S -m "Test branch protection enforcement"
git push -u origin test-protection
```

If commit signing fails here, fix local GPG/SSH signing first.

### 3) Verify enforcement in PR
Open a PR from `test-protection` to `main` and confirm:
- signed commit is recognized
- required checks appear and pass (`API Tests`, `Auto Copilot Review`)
- merge remains blocked until policy requirements are satisfied

## Contributing
This repository is maintained by the owner. Contributions should follow repository security and workflow policies.

## License
Add your preferred license (for example: MIT).
