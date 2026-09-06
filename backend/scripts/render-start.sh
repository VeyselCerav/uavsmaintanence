#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput

if [ "${SEED_DEMO:-false}" = "true" ]; then
  already_seeded="$(python -c "import django; django.setup(); from django.contrib.auth import get_user_model; print('yes' if get_user_model().objects.exists() else 'no')")"
  if [ "$already_seeded" = "yes" ]; then
    echo "SEED_DEMO: kullanıcılar mevcut, seed atlandı."
  else
    python manage.py seed_rbac
    python manage.py seed_dev_user
    python manage.py seed_fleet
  fi
fi

# Render Free ~512 MB: tek worker bellek baskısını ve takılmayı azaltır.
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-1}" --threads 2 --timeout 120
