from django.core.management.base import BaseCommand
from matchmaking.models import Player, PlayerStatistics
from server_side_pong.models import Game
from users.models import Friendship
from django.contrib.auth import get_user_model
import random

User = get_user_model()

class Command(BaseCommand):
	help = "Set up initial data: players, games, and friendships"

	def handle(self, *args, **kwargs):
		# Définir le mot de passe par défaut
		default_password = "SaluT12345!"

		# Créer des utilisateurs (et leurs joueurs associés via le signal)
		for i in range(1, 6):  # Exemple : créer 5 utilisateurs
			username = f"user{i}"
			email = f"user{i}@example.com"
			if not User.objects.filter(username=username).exists():
				user = User.objects.create_user(username=username, email=email)
				user.set_password(default_password)  # Définir le mot de passe ici
				user.save()  # Sauvegarder l'utilisateur après avoir défini le mot de passe
				self.stdout.write(f"Created user: {username} with password: {default_password}")
			else:
				self.stdout.write(f"User {username} already exists")

		# Associer des joueurs à des parties
		players = list(Player.objects.all())
		if len(players) < 2:
			self.stdout.write("Not enough players to create games")
			return

		for i in range(1, 11):  # Exemple : créer 10 jeux
			player1 = random.choice(players)
			player2 = random.choice([p for p in players if p != player1])
			
			# Choisir un gagnant aléatoire entre player1 et player2
			winner = random.choice([player1, player2])
			
			# Créer le jeu avec un gagnant
			game = Game.objects.create(
				name=f"Test Game {i}",
				player1=player1,
				player2=player2,
				rounds_needed=random.randint(1, 5),
				status="completed",
				game_type="remote",
				winner=winner
			)
			print(f"Created game: {game.name} between {player1.nickname} and {player2.nickname}, Winner: {winner.nickname}")
			self.stdout.write(f"Created game: {game.name} between {player1.nickname} and {player2.nickname}")

		# Créer des relations d'amitié aléatoires entre les joueurs
		created_friendships = set()
		for _ in range(10):  # Exemple : essayer de créer 10 amitiés
			player1 = random.choice(players)
			player2 = random.choice([p for p in players if p != player1])

			# Éviter les duplications
			if (player1.id, player2.id) in created_friendships or (player2.id, player1.id) in created_friendships:
				continue

			# Vérifier si l'amitié existe déjà
			if not Friendship.objects.filter(from_user=player1.user, to_user=player2.user).exists():
				Friendship.objects.create(from_user=player1.user, to_user=player2.user, has_rights=True)
				created_friendships.add((player1.id, player2.id))
				print(f"Created friendship between {player1.nickname} and {player2.nickname}")
				self.stdout.write(f"Created friendship between {player1.nickname} and {player2.nickname}")