from django.urls import path

from . import consumers


websocket_urlpatterns = [
	path("ws/chat/<str:room_name>/", consumers.ChatConsumer.as_asgi()),
	#re_path(r'ws/private-chat/(?P<userID>\w+)/$', consumers.PrivateChatConsumer.as_asgi()),
]