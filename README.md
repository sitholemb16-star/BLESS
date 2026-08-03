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
DONOR_DEVICE_SERIAL="<your-donor-device-serial>"
./scripts/pull-apks --serial "$DONOR_DEVICE_SERIAL"
```

The package list lives in `apks/packages.txt`. The script skips packages that are no longer installed on the device.

### Regenerate hashes
```bash
./scripts/hash-apks
```

### Build provenance JSON from Samsung backup manifests
```bash
APP_MANIFEST_1="<path-to-first-app-csv>"
APP_MANIFEST_2="<path-to-second-app-csv>"
APP_MANIFEST_3="<path-to-third-app-csv>"
DONOR_DEVICE_SERIAL="<your-donor-device-serial>"   # e.g. adb get-serialno
DONOR_DEVICE_MODEL="<your-donor-device-model>"

python3 tools/app_inventory/merge_csv_with_hashes.py \
  --csv "$APP_MANIFEST_1" "$APP_MANIFEST_2" "$APP_MANIFEST_3" \
  --sums apks/SHA256SUMS.txt \
  --device-serial "$DONOR_DEVICE_SERIAL" \
  --device-model "$DONOR_DEVICE_MODEL" \
  --out apks/provenance.json
```

The resulting `apks/provenance.json` links backup metadata to pulled local APK hashes.  
It is treated as generated local evidence and is git-ignored by default.

### Verify against CSV FILE_LIST hashes
```bash
python3 tools/app_inventory/verify_hashes_against_csv.py \
  --csv apks/manifests/APP_*.csv \
  --sums apks/SHA256SUMS.txt \
  --fail-on-mismatch
```

## Galaxy S25 Emulator Setup (External Storage)

Use the external sparsebundle-backed path for AVD storage:

- AVD home: `<EXTERNAL_AVD_HOME>`
- AVD name: `Galaxy-S25-128GB`

Create/update the AVD:
```bash
EXTERNAL_AVD_HOME="<external-avd-home>"
ANDROID_SDK_ROOT="<android-sdk-root>"
ANDROID_AVD_HOME="$EXTERNAL_AVD_HOME" ANDROID_SDK_ROOT="$ANDROID_SDK_ROOT" ./scripts/setup-s25-avd
```

Launch it:
```bash
ANDROID_AVD_HOME="$EXTERNAL_AVD_HOME" ANDROID_SDK_ROOT="$ANDROID_SDK_ROOT" ./scripts/launch-s25
```

Install pulled APK set into the running emulator:
```bash
EMULATOR_SERIAL="${ANDROID_SERIAL:-emulator-5554}"
./scripts/install-apks-to-emulator --serial "$EMULATOR_SERIAL"
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
