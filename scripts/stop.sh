#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
docker compose down
echo 'Services stopped. Database and private files have been preserved.'
