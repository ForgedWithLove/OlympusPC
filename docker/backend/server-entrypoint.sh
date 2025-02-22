#!/bin/sh

until cd /app/backend 
do
    echo "Waiting for server volume..."
done


until python manage.py migrate # Запускаем миграции БД
do
    echo "Waiting for db to be ready..."
    sleep 2
done

python manage.py collectstatic --noinput # Собираем статику в один каталог

python manage.py addsuperuser # Добавляем суперпользователя (см. addsuperuser.py)

python manage.py parsecomponents # Собираем данные о комплектующих (см. parsecomponents.py)

gunicorn backend.wsgi --bind 0.0.0.0:8000 --workers 4 --threads 4 # Запускаем сервер
