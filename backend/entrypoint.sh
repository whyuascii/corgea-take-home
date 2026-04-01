#!/bin/sh
set -e

echo "Waiting for database..."
while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('${DB_HOST:-db}', ${DB_PORT:-5432}))
s.close()
" 2>/dev/null; do
    sleep 1
done
echo "Database ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Registering periodic schedules..."
python manage.py register_schedules

# Run Django deployment checklist — surfaces misconfigurations early.
# In development (DJANGO_SETTINGS_MODULE=config.settings.local) this is
# advisory; in production it will catch missing ALLOWED_HOSTS, SECRET_KEY,
# HTTPS settings, etc.
echo "Running deploy checks..."
python manage.py check --deploy 2>&1 || true

if [ "${DJANGO_ENV:-development}" = "production" ]; then
    echo "Starting gunicorn..."
    exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-4}" \
        --max-requests 1000 \
        --max-requests-jitter 50 \
        --timeout 120 \
        --graceful-timeout 30 \
        --access-logfile - \
        --error-logfile -
else
    echo "Starting dev server..."
    exec python manage.py runserver 0.0.0.0:8000
fi
