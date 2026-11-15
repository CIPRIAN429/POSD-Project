#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
docker compose exec -T web python scripts/export-guide.py --check
docker compose exec -T policy python -m pytest -q -p no:cacheprovider
docker compose exec -T web python -m pytest -q -p no:cacheprovider
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py makemigrations --check --dry-run
