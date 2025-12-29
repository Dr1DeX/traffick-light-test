import os

import django
from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = 'org.entrypoints.main.settings'

django.setup()

application = get_wsgi_application()
