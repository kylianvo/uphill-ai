#!/usr/bin/env bash
set -euo pipefail
ANDROID_NATIVE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -f "$ANDROID_NATIVE_DIR/keystore.properties" ]]; then
  printf '%s\n' 'Set android-native/keystore.properties (storeFile, storePassword, keyAlias, keyPassword) before building.' >&2
  exit 1
fi
cd "$ANDROID_NATIVE_DIR"
./gradlew lint testReleaseUnitTest assembleRelease
SDK_DIR="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
if [[ -z "$SDK_DIR" && -f local.properties ]]; then SDK_DIR="$(sed -n 's/^sdk.dir=//p' local.properties)"; fi
APKSIGNER="$(find "$SDK_DIR/build-tools" -name apksigner -type f | sort | tail -1)"
APK="$ANDROID_NATIVE_DIR/app/build/outputs/apk/release/app-release.apk"
EXPECTED_CERT='10:04:51:3F:A6:18:44:EA:42:D1:E0:17:D7:61:66:1F:6F:E8:6E:84:3D:46:67:23:E8:0C:51:20:9E:A4:18:72'
ACTUAL_CERT="$("$APKSIGNER" verify --print-certs "$APK" | sed -n 's/.*certificate SHA-256 digest: //p' | sort -u | tr -d ':' | tr '[:lower:]' '[:upper:]')"
if [[ "$ACTUAL_CERT" != "${EXPECTED_CERT//:/}" ]]; then printf '%s\n' 'Release certificate does not match the existing Capacitor app.' >&2; exit 1; fi
AAPT="$(dirname "$APKSIGNER")/aapt"
BADGING="$("$AAPT" dump badging "$APK" | sed -n '1p')"
[[ "$BADGING" == *"name='ai.uphill.app'"* ]] || { printf '%s\n' 'Incorrect application ID' >&2; exit 1; }
VERSION_CODE="$(printf '%s' "$BADGING" | sed -n "s/.*versionCode='\([0-9]*\)'.*/\1/p")"
(( VERSION_CODE > 6 )) || { printf '%s\n' 'versionCode must upgrade the Capacitor release.' >&2; exit 1; }
DESTINATION="${1:-$HOME/Desktop/Uphill-AI-2.0.0.apk}"
cp "$APK" "$DESTINATION"
printf 'Verified signed APK: %s\n' "$DESTINATION"
