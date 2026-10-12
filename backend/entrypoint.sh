#!/bin/sh
set -e

python manage.py migrate
python manage.py seed_data

PORT="${PORT:-8000}"
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}"
