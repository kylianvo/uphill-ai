#!/usr/bin/env bash
# ==============================================================================
# Uphill AI - Automated Android Release APK Build Script
# ==============================================================================
# Usage:
#   bash scripts/build_android_apk.sh
#
# This script:
#   1. Verifies prerequisites (Node.js, Java, Android SDK, Keystore)
#   2. Builds the Next.js static production bundle (`frontend/out`)
#   3. Syncs native Capacitor assets and plugins (`npx cap sync android`)
#   4. Compiles and signs the release APK with Gradle
#   5. Verifies the generated APK and prints the output path and SHA256
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${REPO_ROOT}/frontend"
ANDROID_DIR="${FRONTEND_DIR}/android"
OUTPUT_APK="${ANDROID_DIR}/app/build/outputs/apk/release/app-release.apk"

# Colors for terminal output
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

info() {
    echo -e "${BLUE}[INFO]${RESET} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${RESET} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${RESET} $*"
}

error() {
    echo -e "${RED}[ERROR]${RESET} $*" >&2
}

echo -e "${BOLD}==============================================================================${RESET}"
echo -e "${BOLD}         Uphill AI - Building Android Release APK (${GREEN}Latest Changes${RESET})         ${RESET}"
echo -e "${BOLD}==============================================================================${RESET}"

# 1. Check Node.js
info "Checking Node.js environment..."
if ! command -v node >/dev/null 2>&1; then
    # Try common nvm path if running in non-interactive shell
    if [ -f "$HOME/.nvm/versions/node/v22.18.0/bin/node" ]; then
        export PATH="$HOME/.nvm/versions/node/v22.18.0/bin:$PATH"
    fi
fi

if ! command -v node >/dev/null 2>&1; then
    error "Node.js is not found in PATH. Please install Node.js (v20+)."
    exit 1
fi
success "Node.js version: $(node -v)"

# 2. Check Java / JDK
info "Checking Java environment..."
if ! command -v java >/dev/null 2>&1; then
    # Check macOS common JVM paths
    if [ -d "/Library/Java/JavaVirtualMachines" ]; then
        LATEST_JAVA="$(find /Library/Java/JavaVirtualMachines -maxdepth 2 -name "Home" 2>/dev/null | head -n 1 || true)"
        if [ -n "$LATEST_JAVA" ]; then
            export JAVA_HOME="$LATEST_JAVA"
            export PATH="$JAVA_HOME/bin:$PATH"
        fi
    fi
fi

if ! command -v java >/dev/null 2>&1; then
    error "Java (JDK 17 or 21) is required to build Android apps. Please install OpenJDK or Android Studio."
    exit 1
fi
JAVA_VER="$(java -version 2>&1 | head -n 1)"
success "Java version: ${JAVA_VER}"

# 3. Check Android SDK
info "Checking Android SDK..."
if [ -z "${ANDROID_HOME:-}" ] && [ -z "${ANDROID_SDK_ROOT:-}" ]; then
    if [ -d "$HOME/Library/Android/sdk" ]; then
        export ANDROID_HOME="$HOME/Library/Android/sdk"
        export ANDROID_SDK_ROOT="$ANDROID_HOME"
    fi
fi

if [ -n "${ANDROID_HOME:-}" ]; then
    success "ANDROID_HOME: ${ANDROID_HOME}"
else
    warn "ANDROID_HOME not explicitly set, Gradle will attempt to resolve via local.properties."
fi

# 4. Check Keystore Configuration
info "Verifying release signing configuration..."
if [ ! -f "${ANDROID_DIR}/keystore.properties" ]; then
    warn "keystore.properties not found in ${ANDROID_DIR}. APK will be built unsigned."
else
    success "Release keystore configuration verified: ${ANDROID_DIR}/keystore.properties"
fi

# 5. Build Next.js Web App
info "Building Next.js production web bundle..."
cd "${FRONTEND_DIR}"
npm run build
success "Next.js export successfully generated in frontend/out/"

# 6. Capacitor Android Sync
info "Syncing web assets and native plugins with Capacitor..."
npx cap sync android
success "Capacitor sync complete."

# 7. Compile Release APK with Gradle
info "Running Gradle assembleRelease..."
cd "${ANDROID_DIR}"
chmod +x ./gradlew
./gradlew assembleRelease --stacktrace

# 8. Verify Built Artifact
if [ -f "${OUTPUT_APK}" ]; then
    APK_SIZE="$(du -h "${OUTPUT_APK}" | awk '{print $1}')"
    APK_MD5="$(md5 -q "${OUTPUT_APK}" 2>/dev/null || md5sum "${OUTPUT_APK}" | awk '{print $1}')"

    echo -e "\n${BOLD}==============================================================================${RESET}"
    echo -e "${GREEN}${BOLD}✓ Android Release APK Successfully Built!${RESET}"
    echo -e "${BOLD}==============================================================================${RESET}"
    echo -e "  Artifact:  ${BOLD}${OUTPUT_APK}${RESET}"
    echo -e "  Size:      ${BOLD}${APK_SIZE}${RESET}"
    echo -e "  MD5:       ${BOLD}${APK_MD5}${RESET}"
    echo -e "=============================================================================="
    echo -e "Next steps:"
    echo -e "  1. Install directly on connected phone:"
    echo -e "     ${BLUE}adb install -r ${OUTPUT_APK}${RESET}"
    echo -e "  2. Or upload ${BOLD}app-release.apk${RESET} to Google Drive link:"
    echo -e "     ${BLUE}https://drive.google.com/file/d/17lt8-S1eeyAbUbyR-QSlkr_kBilNnTKB/view?usp=sharing${RESET}"
    echo -e "==============================================================================\n"
else
    error "Build finished but output APK not found at ${OUTPUT_APK}"
    exit 1
fi
