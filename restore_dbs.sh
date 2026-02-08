#!/usr/bin/env bash
set -euo pipefail

echo "=== Stopping containers and removing volumes ==="
docker compose down -v

echo "=== Starting containers ==="
docker compose up -d