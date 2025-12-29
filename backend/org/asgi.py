"""
ASGI config for org project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

import django
from channels.routing import get_default_application
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'org.settings')

django.setup()

application = SentryAsgiMiddleware(get_default_application())
