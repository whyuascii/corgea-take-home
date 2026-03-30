#!/bin/sh
set -e

echo "Waiting for database..."
while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('db', 5432))
s.close()
" 2>/dev/null; do
    sleep 1
done
echo "Database ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting dev server..."
python manage.py runserver 0.0.0.0:8000
