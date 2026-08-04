release: python manage.py migrate --noinput && python manage.py bootstrap_admin
web: gunicorn config.wsgi:application --workers 3 --timeout 120
