# Команда manage.py addsuperuser предназначена для добавления суперпользователя при начальной инициализации базы данных.
# Выполняется из модуля server-entrypoint.sh в автоматическом режиме при запуске контейнера.
# Имя, пароль и электронная почта создаваемого суперпользователя берутся из переменных окружения, объявленных в .env, и могут быть изменены.

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dotenv import load_dotenv
from colorama import Fore
import os

class Command(BaseCommand):
    def handle(self, **options):
        load_dotenv()
        superuser_name = os.getenv("DJANGO_SUPERUSER_USERNAME")
        if not User.objects.filter(username=superuser_name).exists():
            print(Fore.CYAN + 'Creating superuser ' + superuser_name + '...')
            User.objects.create_superuser(superuser_name, os.getenv("DJANGO_SUPERUSER_EMAIL"), os.getenv("DJANGO_SUPERUSER_PASSWORD"))
            if User.objects.filter(username=superuser_name).exists():
                print(Fore.GREEN + 'Superuser created successfully!')
            else:
                print(Fore.RED + 'Error occured while creating superuser.')
        else:
            print(Fore.CYAN + 'Superuser ' + superuser_name + ' already exists.')