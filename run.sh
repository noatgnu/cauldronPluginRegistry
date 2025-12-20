#!/bin/sh

# Exit on error
set -e

# Run database migrations
poetry run python manage.py migrate

# Collect static files
poetry run python manage.py collectstatic --noinput

# Start gunicorn
poetry run gunicorn cauldronPluginRegistry.wsgi:application --bind 0.0.0.0:8000
