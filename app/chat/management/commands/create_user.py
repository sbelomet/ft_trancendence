from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import Friendship
from matchmaking.models import Player
from server_side_pong.models import Game
import random

class Command(BaseCommand):
	help = 'Create users, friendships and play data'

	def handle(self, *args, **kwargs):
		User = get_user_model()

		# RAW DATA
		user_data = [
			{'username': 'Henry', 'password': 'q', 'email': 'Henry@example.com', 'avatar': 'avatars/default.jpg'},
			{'username': 'Hunter', 'password': 'q', 'email': 'Hunter@example.com', 'avatar': 'avatars/default1.jpg'},
			{'username': 'Jentry', 'password': 'q', 'email': 'Jentry@example.com', 'avatar': 'avatars/default2.jpg'},
			{'username': 'Luz', 'password': 'q', 'email': 'Luz@example.com', 'avatar': 'avatars/default3.jpg'},
			{'username': 'Finn', 'password': 'q', 'email': 'Finn@example.com', 'avatar': 'avatars/default4.jpg'},
			{'username': 'Kipo', 'password': 'q', 'email': 'Kipo@example.com', 'avatar': 'avatars/default5.jpg'},
			{'username': 'Steven', 'password': 'q', 'email': 'Steven@example.com', 'avatar': 'avatars/default6.jpg'},
			{'username': 'Tulip', 'password': 'q', 'email': 'Tulip@example.com', 'avatar': 'avatars/default7.jpg'},
			{'username': 'Aelita', 'password': 'q', 'email': 'Aelita@example.com', 'avatar': 'avatars/default8.jpg'},
			{'username': 'Hilda', 'password': 'q', 'email': 'Hilda@example.com', 'avatar': 'avatars/default7.jpg'},
			{'username': 'Gumball', 'password': 'q', 'email': 'Gumball@example.com', 'avatar': 'avatars/default6.jpg'},
			{'username': 'Gwen', 'password': 'q', 'email': 'Gwen@example.com', 'avatar': 'avatars/default5.jpg'},
			{'username': 'Dipper', 'password': 'q', 'email': 'Dipper@example.com', 'avatar': 'avatars/default4.jpg'},
			{'username': 'Mabel', 'password': 'q', 'email': 'Mabel@example.com', 'avatar': 'avatars/default3.jpg'},
			{'username': 'Amity', 'password': 'q', 'email': 'Amity@example.com', 'avatar': 'avatars/default2.jpg'},
			{'username': 'Jake', 'password': 'q', 'email': 'Jake@example.com', 'avatar': 'avatars/default1.jpg'},
			{'username': 'Hooty', 'password': 'q', 'email': 'Hooty@example.com', 'avatar': 'avatars/default.jpg'},
			{'username': 'Pomni', 'password': 'q', 'email': 'Pomni@example.com', 'avatar': 'avatars/default.jpg'},
			{'username': 'Reagan', 'password': 'q', 'email': 'Reagan@example.com', 'avatar': 'avatars/default8.jpg'},
			{'username': 'Ekko', 'password': 'q', 'email': 'Ekko@example.com', 'avatar': 'avatars/default3.jpg'},
		]

		# USER CREATION
		users = {}
		for user in user_data:
			if not User.objects.filter(username=user['username']).exists():
				created_user = User.objects.create_user(
					username=user['username'],
					password=user['password'],
					email=user['email'],
					avatar=user['avatar']
				)
				users[user['username']] = created_user
				self.stdout.write(self.style.SUCCESS(f"Successfully created user \"{user['username']}\" with password \"{user['password']}\""))
			else:
				users[user['username']] = User.objects.get(username=user['username'])
				self.stdout.write(self.style.WARNING(f"User \"{user['username']}\" already exists"))

		# FRIENDSHIP CREATION
		friendships = set()
		for user in users.keys():
			other_users = [u for u in users.keys() if u != user]
			num_friends = random.randint(1, 3)
			friends = random.sample(other_users, num_friends)
			for friend in friends:
				if (friend, user) not in friendships:
					friendships.add((user, friend))

		for from_user, to_user in friendships:
			from_user_instance = users[from_user]
			to_user_instance = users[to_user]

			if not Friendship.objects.filter(from_user=from_user_instance, to_user=to_user_instance).exists():
				Friendship.objects.create(from_user=from_user_instance, to_user=to_user_instance, has_rights=True)
				self.stdout.write(self.style.SUCCESS(f'Successfully created friendship between \"{from_user}\" and \"{to_user}\"'))
			else:
				self.stdout.write(self.style.WARNING(f'Friendship between \"{from_user}\" and \"{to_user}\" already exists'))
		
		# PLAY DATA CREATION
		players = list(Player.objects.all())
		if len(players) < 2:
			self.stdout.write(self.style.WARNING("Not enough players to create games"))
			return

		for i in range(15):
			player1 = random.choice(players)
			player2 = random.choice([p for p in players if p != player1])	
			winner = random.choice([player1, player2])
			game_name = f"Test Game {i + 1}"
			
			if not Game.objects.filter(name=game_name).exists():
				game = Game.objects.create(
					name=game_name,
					player1=player1,
					player2=player2,
					start_time=timezone.now(),
					end_time=timezone.now(),
					rounds_needed=3,
					status="completed",
					created_at=timezone.now(),
					game_type="remote",
					winner=winner
				)
				self.stdout.write(self.style.SUCCESS(f'Successfully created game \"{game.name}\" between \"{player1.nickname}\" and \"{player2.nickname}\" with winner \"{winner.nickname}\"'))
			else:
				self.stdout.write(self.style.WARNING(f'Game \"{game_name}\" already exists'))