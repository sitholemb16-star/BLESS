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

## Definition of Done

The process is complete when the dataset is no longer just technical artifacts, but a coherent and navigable record of communication and activity from top to bottom.
