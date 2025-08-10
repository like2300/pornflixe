#!/usr/bin/env bash
# Exit on any error
set -e

python3.11 -m pip install --upgrade pip
python3.11 -m pip install -r requirements.txt

# Apply database migrations
python3.11 manage.py migrate

# Collect static files
python3.11 manage.py collectstatic --noinput

# Create superuser (improved version)
echo "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='root').exists():
    User.objects.create_superuser(
        os.getenv('DJANGO_SUPERUSER_USERNAME', 'root'),
        os.getenv('DJANGO_SUPERUSER_EMAIL', 'root@example.com'),
        os.getenv('DJANGO_SUPERUSER_PASSWORD', 'root')
    )
" | python3.11 manage.py shell