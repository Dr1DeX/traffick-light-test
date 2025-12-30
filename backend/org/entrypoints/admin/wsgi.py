import os

from django.core.wsgi import get_wsgi_application
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "orgs.entrypoints.admin.settings"

django.setup()

application = get_wsgi_application()
