#!/usr/bin/env bash
set -o errexit

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-scraphounds.settings.production}"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

pushd junkyardFinder/static_src
npm ci
npm run build
popd

python manage.py collectstatic --no-input
