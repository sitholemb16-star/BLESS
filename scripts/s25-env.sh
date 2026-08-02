#!/usr/bin/env bash
# s25-env.sh — Shared Galaxy S25 AVD environment setup.
# Source this file (do not execute it directly).
#
# Usage:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   # shellcheck source=scripts/s25-env.sh
#   source "$SCRIPT_DIR/s25-env.sh"
#
# After sourcing, SDK_ROOT, AVD_HOME, AVD_NAME, and JAVA_HOME are set and
# JAVA_HOME / ANDROID_SDK_ROOT / ANDROID_AVD_HOME are exported.
# Callers must extend PATH themselves (each script needs a different subset
# of SDK tool directories).

# SDK root: ANDROID_SDK_ROOT must be set explicitly — no machine-specific fallback.
if [[ -z "${ANDROID_SDK_ROOT:-}" ]]; then
  echo "ERROR: ANDROID_SDK_ROOT is not set. Export it before sourcing this file." >&2
  return 1
fi
SDK_ROOT="$ANDROID_SDK_ROOT"

AVD_NAME="${AVD_NAME:-Galaxy-S25-128GB}"

# AVD home must be set via ANDROID_AVD_HOME; there is no portable fallback.
if [[ -z "${ANDROID_AVD_HOME:-}" ]]; then
  echo "ERROR: ANDROID_AVD_HOME is not set. Export it before sourcing this file." >&2
  return 1
fi
AVD_HOME="$ANDROID_AVD_HOME"

if [[ -n "${JAVA_HOME:-}" ]]; then
  : # already set by the caller — use it as-is
elif command -v java >/dev/null 2>&1; then
  # Resolve JAVA_HOME from the runtime on PATH (portable across macOS/Linux).
  # Manually follow symlinks; readlink on macOS does not support -f.
  _java_bin="$(command -v java)"
  while [[ -L "$_java_bin" ]]; do
    _link="$(readlink "$_java_bin")"
    if [[ "$_link" = /* ]]; then
      _java_bin="$_link"
    else
      _java_bin="$(cd "$(dirname "$_java_bin")" && pwd)/$_link"
    fi
  done
  _java_bin="$(cd "$(dirname "$_java_bin")" && pwd)/$(basename "$_java_bin")"
  JAVA_HOME="$(cd "$(dirname "$_java_bin")/.." && pwd)"
  unset _java_bin _link
else
  echo "ERROR: JAVA_HOME is not set and java is not on PATH." >&2
  return 1
fi

# Validate that the resolved JAVA_HOME actually contains a java executable.
if [[ ! -x "$JAVA_HOME/bin/java" ]]; then
  echo "ERROR: JAVA_HOME resolved to '$JAVA_HOME' but '$JAVA_HOME/bin/java' is not executable." >&2
  return 1
fi

export JAVA_HOME
export ANDROID_SDK_ROOT="$SDK_ROOT"
export ANDROID_AVD_HOME="$AVD_HOME"
