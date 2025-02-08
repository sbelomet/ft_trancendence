"""
ASGI config for hello_django project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter # is used to route incoming connections based on their protocol type, like http or websocket.
from channels.auth import AuthMiddlewareStack #This middleware provides authentication support for WebSocket connections, ensuring that connections have access to user information.
from django.core.asgi import get_asgi_application
from users.middleware.websocket_middleware import JWTAuthMiddlewareWS

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hello_django.settings')
django_asgi_app = get_asgi_application()

import chat.routing
import server_side_pong.routing

application = ProtocolTypeRouter(
	{
		"http": django_asgi_app,
		"websocket": JWTAuthMiddlewareWS(
			URLRouter(
				chat.routing.websocket_urlpatterns +
				server_side_pong.routing.websocket_urlpatterns
			)),
	}
)