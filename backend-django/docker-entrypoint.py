"""Prepara o SQLite e inicia o servidor de desenvolvimento do trabalho."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estacionamento.settings')

    from django.conf import settings

    database_path = Path(settings.DATABASES['default']['NAME'])
    database_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [sys.executable, 'manage.py', 'migrate', '--noinput'], check=True
    )
    os.execv(
        sys.executable,
        [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8080', '--noreload'],
    )


if __name__ == '__main__':
    main()
