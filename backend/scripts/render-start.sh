#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput
python manage.py seed_rbac

if [ "${SEED_DEMO:-false}" = "true" ]; then
  already_users="$(python -c "import django; django.setup(); from django.contrib.auth import get_user_model; print('yes' if get_user_model().objects.exists() else 'no')")"
  if [ "$already_users" = "no" ]; then
    python manage.py seed_dev_user
  else
    echo "SEED_DEMO: kullanıcılar mevcut, seed_dev_user atlandı."
  fi
fi

python manage.py seed_fleet

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-1}" --threads 2 --timeout 120
