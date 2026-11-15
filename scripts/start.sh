#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v docker >/dev/null || { echo 'Docker is required.'; exit 1; }
docker compose version >/dev/null 2>&1 || { echo 'Docker Compose is required. On Ubuntu: sudo apt install docker-compose-v2'; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Docker Engine is not available. Start Docker and try again.'; exit 1; }
if [[ ! -f .env ]]; then
  umask 077
  secret() { od -An -N32 -tx1 /dev/urandom | tr -d ' \n'; }
  printf 'DJANGO_SECRET_KEY=%s\nPOSTGRES_PASSWORD=%s\nPOLICY_API_KEY=%s\nDEMO_PASSWORD=LearnTogether2026!\nAPP_PORT=8000\n' "$(secret)" "$(secret)" "$(secret)" > .env
fi
docker compose up --build -d --wait --wait-timeout 240
app_port=${APP_PORT:-$(sed -n 's/^APP_PORT=//p' .env | tail -n 1)}
printf '\nAccess Granted is ready: http://localhost:%s\n' "${app_port:-8000}"
echo 'Demo users: atlas.admin, atlas.instructor, atlas.student1, atlas.student2, atlas.student3'
echo '            nova.admin, nova.instructor, nova.student1, nova.student2, nova.student3'
echo 'Platform administration: superadmin at /admin/'
echo 'Initial demo password: see DEMO_PASSWORD in your local .env file.'
echo 'Existing accounts and data are preserved on every restart.'
