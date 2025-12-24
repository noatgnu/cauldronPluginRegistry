#!/bin/sh

# Exit on error
set -e

# Run database migrations
poetry run python manage.py migrate

# Collect static files
poetry run python manage.py collectstatic --noinput

# Create initial superuser if one does not exist and environment variables are set
if [ -n "$ADMIN_USER" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "Creating initial superuser..."
    poetry run python manage.py create_initial_superuser
else
    echo "ADMIN_USER or ADMIN_PASSWORD not set. Skipping initial superuser creation."
fi

# Start gunicorn
poetry run gunicorn cauldronPluginRegistry.wsgi:application --bind 0.0.0.0:8000
