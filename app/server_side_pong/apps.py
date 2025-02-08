from django.apps import AppConfig

class ServerSidePongConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'server_side_pong'

    def ready(self):
        # Import models during app initialization to ensure readiness -> import model issue solved
        from .models import Game
        from users.models import CustomUser
        self.game_model = Game
        