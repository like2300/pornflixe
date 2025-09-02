#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='root').delete(); User.objects.create_superuser('root', 'root@example.com', 'root')" | python manage.py shell
python manage.py check