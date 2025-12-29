from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
    }
)

application = SentryAsgiMiddleware(application)
