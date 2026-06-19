#!/bin/bash
# Exit on any error
set -e

# Make sure we are in the script's directory
cd "$(dirname "$0")"

echo "🛑 Stopping and removing any running Docker containers for vibrant-newton..."
docker compose down || true

echo "📁 Moving up to the parent directory..."
cd ..

echo "🔄 Renaming directory 'vibrant-newton' to 'uphill-ai'..."
if [ -d "uphill-ai" ]; then
    echo "⚠️ Error: A directory named 'uphill-ai' already exists. Aborting."
    exit 1
fi
mv vibrant-newton uphill-ai

echo "📂 Navigating to new project root 'uphill-ai'..."
cd uphill-ai

echo "🐍 Recreating Python virtual environment (to update hardcoded paths)..."
rm -rf backend/.venv
python3 -m venv backend/.venv

echo "📦 Installing backend dependencies..."
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "✨ Done! Project successfully renamed to 'uphill-ai'."
echo "👉 You can now open the new path in your IDE:"
echo "   /Users/vietvo/Documents/antigravity/uphill-ai"
