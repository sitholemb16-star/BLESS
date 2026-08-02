#!/usr/bin/env bash
# s25-env.sh — Shared Galaxy S25 AVD environment setup.
# Source this file (do not execute it directly).
#
# Usage:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   # shellcheck source=scripts/s25-env.sh
#   source "$SCRIPT_DIR/s25-env.sh"
#
# After sourcing, EXTERNAL, SDK_ROOT, AVD_HOME, AVD_NAME, and JAVA_HOME are
# set and JAVA_HOME / ANDROID_SDK_ROOT / ANDROID_AVD_HOME are exported.
# Callers must extend PATH themselves (each script needs a different subset
# of SDK tool directories).

EXTERNAL="${EXTERNAL:-/Volumes/Secure AI Coding Tools}"
SDK_ROOT="${ANDROID_SDK_ROOT:-$EXTERNAL/Android/sdk}"
AVD_HOME="${ANDROID_AVD_HOME:-/Volumes/VOLUME 1/2027 Final Drafts.sparsebundle/android-avd}"
AVD_NAME="Galaxy-S25-128GB"

if [[ -n "${JAVA_HOME:-}" ]]; then
  JAVA_HOME="${JAVA_HOME}"
elif [[ -d "/opt/homebrew/opt/openjdk" ]]; then
  JAVA_HOME="/opt/homebrew/opt/openjdk"
else
  JAVA_HOME="/usr/local/opt/openjdk"
fi

export JAVA_HOME
export ANDROID_SDK_ROOT="$SDK_ROOT"
export ANDROID_AVD_HOME="$AVD_HOME"
