#!/bin/bash
# Deploy script: pull latest code and rebuild Docker
set -e

cd "$(dirname "$0")"

echo ">>> Fetching latest..."
git fetch --all

echo ">>> Pulling..."
git pull

echo ">>> Building..."
docker compose build

echo ">>> Starting..."
docker compose up -d

echo ">>> Done. App at http://$(hostname -I 2>/dev/null | awk '{print $1}'):8000"
