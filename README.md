# Data Reconstruction Workflow

This repository documents a practical workflow for turning hashed, seemingly meaningless backup files into a readable, chronological record of messages and app activity.

## Current State

The dataset has already moved past the raw-ingest stage:

1. **Signature inspection completed**
    - Files were identified by content signatures (not filenames).
    - Most hashed files were recognized as compressed archives, plus images and structured text.
2. **Archive normalization and extraction completed**
    - Archive-type files were renamed to usable formats.
    - Each archive was extracted into its own folder.
    - The dataset now exposes internal app storage artifacts (databases, XML/JSON, media).

This confirms the data was not lost or encrypted; it was packaged and renamed.

## Android Emulator Communication Testing

The repository includes a small `adb` harness for exercising cellular call and
SMS flows without adding an Android application or test framework:

```bash
# Verify the selected target.
scripts/emulator-comm --serial emulator-5554 status

# Exercise outgoing flows on an emulator or connected Android device.
scripts/emulator-comm --serial emulator-5554 dial +15551234567
scripts/emulator-comm --serial emulator-5554 compose-sms +15551234567 "Test message"

# Inject incoming events into an Android Emulator.
scripts/emulator-comm --serial emulator-5554 incoming-call +15557654321
scripts/emulator-comm --serial emulator-5554 accept-call +15557654321
scripts/emulator-comm --serial emulator-5554 reject-call +15557654321
scripts/emulator-comm --serial emulator-5554 incoming-sms +15557654321 "Incoming test"

# End the currently active call.
scripts/emulator-comm --serial emulator-5554 end-call
```

Install Android SDK Platform-Tools, start an Android Virtual Device with
cellular services, and confirm it appears in `adb devices` before running the
commands. `ANDROID_SERIAL` can be used instead of `--serial`.

`/Volumes/VOLUME 1/2027 Final Drafts.sparsebundle` is the encrypted macOS disk
image backing the mounted workspace; it is a storage location, not an Android
AVD or emulator executable. Do not pass this path to the harness. Continue to
select the running emulator by its `adb` serial.

Incoming event injection uses Android Emulator console commands and is not
available on physical devices. `dial` starts the system call flow; whether it
can connect beyond the emulator depends on the target's telephony service.
`compose-sms` opens a populated SMS composer so the user can confirm the send,
matching Android's permission model. Run `tests/emulator-comm-test` to verify
the harness with a mocked `adb`.

## Objective

Reconstruct all recoverable data into **human-readable, chronological outputs** (for example, conversation timelines with timestamps and linked media), preserving context and sequence.

## Reconstruction Plan

### 1) Consolidate sources
- Merge newly extracted folders with the earlier processed dataset into one working directory.
- De-duplicate by checksum and/or canonical path mapping.
- Keep provenance metadata so every recovered item can be traced to source.

### 2) Classify artifacts
- Group by type:
    - SQLite / other databases
    - XML metadata
    - JSON records
    - Media files (images, audio, video, documents)
- Build an inventory table with file path, app/domain guess, timestamp fields, and parse status.

### 3) Prioritize high-value data
- Identify key messaging/social app databases first.
- Locate message tables, contact tables, chat/thread mappings, and attachment references.
- Extract metadata-bearing XML/JSON files that can fill gaps (device/app timestamps, identifiers, mapping keys).

### 4) Parse and normalize
- Convert records from each source format into a unified schema:
    - `source_app`
    - `thread_id`
    - `message_id`
    - `sender`
    - `recipient(s)`
    - `content`
    - `timestamp_original`
    - `timestamp_utc`
    - `attachment_path`
    - `source_file`
- Normalize timestamps to UTC while preserving raw values.

### 5) Correlate and sequence
- Join messages to attachments using IDs, filenames, and path references.
- Resolve cross-file relationships (DB ↔ XML/JSON ↔ media).
- Sort into a global timeline and per-thread timelines.

### 6) Validate and export
- Flag duplicates and conflicts for review.
- Produce readable outputs:
    - Per-conversation chat logs
    - Master chronological timeline
    - Media index with message linkage
- Record parser confidence and unresolved references.

## Emulator Communication Harness

A lightweight ADB harness is included at `scripts/emulator-comm`.

### Target selection

- Explicit serial: `--serial <serial>`
- Environment fallback: `ANDROID_SERIAL=<serial>`

### Supported operations

- Connection/status checks (`status`)
- Outgoing call start/end (`call-start`, `call-end`)
- Incoming call inject/accept/reject (`call-incoming`, `call-accept`, `call-reject`)
- Outgoing SMS composer (`sms-send`)
- Incoming SMS injection (`sms-incoming`)

### Usage examples

```bash
# show target and connectivity
scripts/emulator-comm status

# select device explicitly
scripts/emulator-comm --serial emulator-5554 status

# outgoing call
scripts/emulator-comm call-start 15551234567
scripts/emulator-comm call-end

# incoming call simulation (emulator only)
scripts/emulator-comm call-incoming 15557654321
scripts/emulator-comm call-accept 15557654321
scripts/emulator-comm call-reject 15557654321

# outgoing sms composer
scripts/emulator-comm sms-send 15551234567 "hello from harness"

# incoming sms simulation (emulator only)
scripts/emulator-comm sms-incoming 15557654321 "test inbound"
```

### Behavioral notes and limitations

- Primary target is the Android Emulator.
- On physical devices, ADB connectivity commands are supported.
- Incoming call/SMS injection is **not available** on physical devices and is reported explicitly as:
  - `UNSUPPORTED_ON_PHYSICAL_DEVICE: incoming call/SMS injection requires Android Emulator`
- This behavior is a hard failure (non-zero exit), not a silent no-op.

### Path alignment

Emulator path reference is aligned to mounted sparsebundle:

`/Volumes/VOLUME 1/2027 Final Drafts.sparsebundle`

## Definition of Done

The process is complete when the dataset is no longer just technical artifacts, but a coherent and navigable record of communication and activity from top to bottom.
