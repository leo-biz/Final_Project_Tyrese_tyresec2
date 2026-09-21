#!/usr/bin/env bash
set -o errexit

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-scraphounds.settings.production}"

python manage.py migrate --no-input
gunicorn scraphounds.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
