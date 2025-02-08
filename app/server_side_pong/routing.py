from django.urls import path
from server_side_pong.consumers.consumers import LocalPongConsumer, RemotePongConsumer

websocket_urlpatterns = [
	
    # Local games (no game_id in the path)
    path('ws/server_side_pong/local/<int:game_id>/', LocalPongConsumer.as_asgi(), name='local_game'),

    # Remote games (game_id included in the path)
    path('ws/server_side_pong/remote/<int:game_id>/', RemotePongConsumer.as_asgi(), name='remote_game'),
]