#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
echo 'This removes ALL Access Granted application data and restores the demo.'
read -r -p 'Type RESET to continue: ' response
[[ "$response" == RESET ]] || { echo 'Reset cancelled.'; exit 0; }
docker compose exec -T web python manage.py reset_demo --confirm-reset
