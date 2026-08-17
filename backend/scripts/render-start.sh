#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput

if [ "${SEED_DEMO:-false}" = "true" ]; then
  python manage.py seed_rbac
  python manage.py seed_dev_user
  python manage.py seed_fleet
fi

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
