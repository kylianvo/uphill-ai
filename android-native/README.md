# Uphill AI native Android

Kotlin + Jetpack Compose port of `ios-native`, using the same FastAPI endpoints.
Package `ai.uphill.app`, version 2.0.0 (10), minimum Android 8 (API 26).

## Build

Use JDK 17 and an Android SDK with platform 36. Set `ANDROID_HOME` or an ignored
`local.properties` with `sdk.dir=/absolute/path/to/sdk`.

```sh
cd android-native
python3 scripts/test_xcstrings.py
./gradlew lint testDebugUnitTest testReleaseUnitTest assembleDebug
```

Debug defaults to `http://10.0.2.2:8000` (Android emulator → development host).
Run the backend on host port 8000. Use `-PuphillLocalApiPort=8016` for another local port; this changes only the debug build default. For a physical device use `adb reverse tcp:8000 tcp:8000`
and select localhost from the developer environment menu. Long-press the version
in Me to change the debug environment. Release always uses the production URL.

## Translations and fixtures

`python3 scripts/xcstrings_to_android.py` regenerates EN/VI resources and
`string_keys.json` from the iOS catalog. Android-only additions are in
`scripts/extra_strings.json`; feature-specific resources live beside the generated
strings. JVM tests read the existing iOS backend fixtures through Gradle sourceSets.

## Release signing

Set ignored `keystore.properties` using the existing Capacitor release keystore:
`storeFile`, `storePassword`, `keyAlias`, `keyPassword`. Do not commit credentials.
`scripts/build_release_apk.sh [destination]` checks lint and release tests, builds
and verifies the certificate, package and upgrade version, then copies the APK to
Desktop by default. Both release and old APK must use the same certificate.

Google uses Credential Manager with the existing web server client ID. Google Cloud
must register package `ai.uphill.app` with release SHA-1
`97:AF:6B:43:56:8F:E3:88:06:B7:E7:AA:37:1A:D4:E5:F8:91:FB:6F`.
A separate debug-certificate OAuth client is needed for Google login in debug APKs.
COROS uses Custom Tabs and `uphillai://coros/callback`, validating a one-use state.

Feature packages depend on Core and DesignSystem. Application composition and
navigation live in `app/`. Per-screen ViewModels own StateFlow; dependencies are
constructed manually. No Hilt. This branch also includes two backend profile fixes:
saved athlete notes are returned, and omitted API keys survive profile edits.

See [handoff](docs/HANDOFF.md) for verification and remaining manual checks, and
[emulator evidence](docs/screenshots/parity-2026-10-15/README.md) for EN/VI captures.
The PR remains draft while complete iOS parity and live OAuth/device checks are pending.

Body typography uses the bundled Plus Jakarta Sans variable font (weight axis200–800),
as requested. Monospaced labels retain `FontFamily.Monospace`. The same font file is
bundled by iOS for launch, while iOS body text uses its platform face; this choice
does not establish exact iOS glyph matching. See [font license](licenses/README.md).
