#!/bin/sh
set -e

python manage.py migrate
python manage.py seed_data

PORT="${PORT:-8000}"
# exec reemplaza el proceso sh por gunicorn (PID 1), para que reciba SIGTERM
# directo en los redeploys/restarts de Render en vez de quedar huerfano.
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --timeout 120
