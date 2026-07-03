#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Restore default media files if missing
mkdir -p media/products
mkdir -p media/screenshots
cp -rn media_backup/* media/ 2>/dev/null || true

python manage.py collectstatic --no-input
python manage.py migrate

