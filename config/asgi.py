"""
ASGI config for kiosc project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import django
from django.core.asgi import get_asgi_application

django.setup()


from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

# Needs to be loaded before importing from apps

import containers.urls


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(containers.urls.websocket_urlpatterns)
        ),
    }
)
