#!/bin/sh
# Runs every time the web container starts.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
