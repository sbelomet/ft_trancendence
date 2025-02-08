from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Friendship
from matchmaking.models import Player
from server_side_pong.models import Game
class Command(BaseCommand):
	help = 'Clear game, friendship and user models data'

	def handle(self, *args, **kwargs):
		Game.objects.all().delete()
		self.stdout.write(self.style.SUCCESS('Successfully cleared Game data'))

		Friendship.objects.all().delete()
		self.stdout.write(self.style.SUCCESS('Successfully cleared Friendship data'))

		Player.objects.all().delete()
		self.stdout.write(self.style.SUCCESS('Successfully cleared Player data'))

		User = get_user_model()
		User.objects.all().delete()
		self.stdout.write(self.style.SUCCESS('Successfully cleared User data'))