from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from server_side_pong.models import Game
from django.db.models import Sum
import random
import logging
from django.db import transaction
from django.db.models import F, FloatField, ExpressionWrapper, Value, Case, When
from django.db.models.functions import Coalesce, Ln

logger = logging.getLogger(__name__)

#Coalesce : check si donnée non dispo dans db (valeur NULL), et retourne 0 à la place.
# permet de garantir le fait de ne pas faire de calcule avec valeur null 
# (ex: matches_played = NULL, devient 0 / matches_played = 5 reste 5)

#La fonction F de django fait référence à un champ dans la db pour faire requete directement dedans
# permet d’effectuer  des opérations en base de données sans avoir à les récupérer 
# préalablement de la base de données vers la mémoire Python

#ExpressionWrapper permet de transformer des valeurs différentes entre l'input et l'output définit dans output_field
#ex entre des int qui divisés entre eux deviennent des float
class PlayerManager(models.Manager):
	def get_ranked_players(self):
		return self.annotate(
			matches_played=Coalesce(F('stats__matches_played'), 0),

			matches_won=Coalesce(F('stats__matches_won'), 0),

			win_ratio=ExpressionWrapper(
				F('matches_won') / Coalesce(F('matches_played'), Value(1)),  # Value(1) évite division par 0
				output_field=FloatField()
			)
		).filter(
			matches_played__gt=0  # ignorer les joueurs sans matchs
		).order_by(
			'-matches_won', #trier d'abord par nrb de match gagné puis par nbr match joué
			'-matches_played'
		)


#a player is automatically created when a user is save using signals
class Player(models.Model):
	id = models.IntegerField(primary_key=True, editable=False) #false pour éviter la perte de liena user associé
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='player_profile'
	)
	nickname = models.CharField(max_length=50, unique=True)
	ranking = models.IntegerField(default=0)
	avatar = models.ImageField(upload_to='avatars/', default='avatars/default.jpg')
	objects = PlayerManager()

	@property 
	def match_history(self):
		return Game.objects.filter(models.Q(player1=self) | models.Q(player2=self))
	
	@property 
	def tournament_history(self):
		return Tournament.objects.filter(participants=self)
	 
	def __str__(self):
		return self.user.username
	
	def save(self, *args, **kwargs):
		"""
        Override save to handle remote URLs and local files.
        - If `avatar` is a remote URL, save it directly as a string in the database.
        - If `avatar` is a local file, use Django's default behavior for saving local files.
        """
		if self.avatar and (self.avatar.name.startswith('http://') or self.avatar.name.startswith('https://')):
            # Save the remote URL directly in the database
			self._avatar = self.avatar.name
			self.avatar.storage = None  # Prevent Django from treating it as a local file
		else:
            # Use the default behavior for local files
			self._avatar = None
		super().save(*args, **kwargs)

#The @property decorator in Python allows you to define methods in a class that
# can be accessed like attributes. This is particularly useful when you want to
# compute a value dynamically based on other fields in the class without storing
# it directly in the database.
#=> le decorateur property fonctionne comme un attribut mais dynamique (méthode déguisée en attribut)
class PlayerStatistics(models.Model):
	player = models.OneToOneField('Player', on_delete=models.CASCADE, related_name='stats')
	matches_played = models.IntegerField(default=0)
	matches_won = models.IntegerField(default=0)

	def __str__(self):
		return f"{self.player.user.username} Statistics"

	@property
	def matches_lost(self):
		return self.matches_played - self.matches_won

	@property
	def win_rate(self):
		played = self.matches_played
		return round((self.matches_won / played) * 100, 2) if played > 0 else 0
	
	@property
	def tournaments_played(self):
		return self.player.tournament_history.count()
	
	@property
	def tournaments_won(self):
		return self.player.tournament_history.filter(winner=self.player).count()
	
	@property
	def tournament_win_rate(self):
		played = self.tournaments_played
		return round((self.tournaments_won / played) * 100, 2) if played > 0 else 0


class Tournament(models.Model):
	STATUS_CHOICES = [
		('upcoming', 'Upcoming'),
		('ongoing', 'Ongoing'),
		('completed', 'Completed'),
	]
	name = models.CharField(max_length=200, unique=True)
	description = models.CharField(max_length=400, default=None, null=True, blank=True)
	participants = models.ManyToManyField(Player, related_name="tournaments")
	bye_player = models.ForeignKey(
		'Player',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='bye_tournaments'
	)
	start_time = models.DateTimeField()
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='upcoming')
	winner = models.ForeignKey('matchmaking.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='tournaments_won')
	created_by = models.ForeignKey('matchmaking.Player', on_delete=models.SET_NULL, null=True, related_name='created_tournaments')
	max_players = models.PositiveIntegerField(default=None, null=True, blank=True, validators=[MinValueValidator(2)])
	current_round = models.PositiveIntegerField(default=1)
	invitations = models.ManyToManyField(
		'Player',
		through='TournamentInvitation',
		through_fields=('tournament', 'to_player'),
		related_name='tournament_invitations',
		blank=True
	)
	games = models.ManyToManyField('server_side_pong.Game', blank=True, related_name='tournaments')


	def __str__(self):
		return self.name

	def generate_initial_matches(self):
		from server_side_pong.consumers.consumers import GameManager
		participants = list(self.participants.all())
		logger.info(f'Participants: {participants}')
		random.shuffle(participants)

		# joueurs impair for round 2
		if len(participants) % 2 != 0:
			self.bye_player = participants.pop()
			self.save()

		# pairs first round
		game_dict = {}
		for i in range(0, len(participants), 2):
			player1 = participants[i]
			player2 = participants[i+1]
			game = Game.objects.create(
				name=f'{self.name}, round {self.current_round} with {player1.nickname} vs {player2.nickname}',
				created_by=player1,
				player1=player1,
				player2=player2,
				rounds_needed=3, # DEFAULT
				status='scheduled',
				game_type='remote',
				tournament=self,
			)
			GameManager.create_game(game.id)
			game_dict[game.id] = (player1.id, player2.id)
			logger.info(f'Game created: {game.id} with players {player1.id} and {player2.id}')
			self.games.add(game)
		logger.info(f'Generated game_dict: {game_dict}')
		return game_dict

#transaction.atomic() permet de garder la db consistente en vérifiant que soit toutes les
#conditions sont réunies pour la mettre à jour soit rien n'est fait
#cela permet de ne pas avoir des matchs a différents stade
	def advance_tournament_round(self):
		from server_side_pong.consumers.consumers import GameManager

		with transaction.atomic():
			# Log all games
			all_games = list(self.games.all())  # Ensure immediate evaluation
			for game in all_games:
				logger.info(f"games in advance: {game}, id: {game.id}, round number: {game.round_number}, current_round: {self.current_round}")

			# Fetch and process previous round games
			previous_round_games = self.games.filter(round_number=self.current_round - 1, status='completed').select_related('winner')
			logger.info(f"previous_round_games??? in advance tournament: {previous_round_games}")

			# Refresh and log each game
			winners = []
			for game in previous_round_games:
				game.refresh_from_db()  # Ensure up-to-date data
				logger.info(f"game {game.id} winner: {game.winner}")
				if game.winner:
					winners.append(game.winner)

			logger.info(f"Winners in advance tournament: {winners}")

			logger.info(f"bye player in advance tournament: {self.bye_player}")
			if self.bye_player:
				winners.append(self.bye_player)
			if len(winners) % 2 != 0 and len(winners) != 1:
				remaining_winners = [winner for winner in winners if winner != self.bye_player]
				self.bye_player = random.choice(remaining_winners)
				winners.remove(self.bye_player)
			else:
				self.bye_player = None
				self.save()

			logger.info(f"winners in advance tournament: {winners}")
			if len(winners) == 1:
				self.winner = winners[0]
				self.status = 'completed'
				self.save()
				logger.info(f"Tournament '{self.name}' completed. Winner: {self.winner.user.username}")
			else:
				self.current_round += 1
				self.save()

				random.shuffle(winners)

				game_dict = {}
				for i in range(0, len(winners), 2):
					player1 = winners[i]
					player2 = winners[i + 1]
					game = Game.objects.create(
						name=f'{self.name}, round {self.current_round} with {player1.nickname} vs {player2.nickname}',
						rounds_needed=3,
						player1=player1,
						player2=player2,
						created_by=player1,
						status='scheduled',
						tournament=self,
						round_number=self.current_round - 1,
					)
					GameManager.create_game(game.id)
					game_dict[game.id] = (player1.id, player2.id)
					self.games.add(game)
					logger.info(f'Game created: {game.id} with players {player1.id} and {player2.id}')
				logger.info(f'Generated game_dict: {game_dict}')
				return game_dict

class TournamentInvitation(models.Model):
	tournament = models.ForeignKey(Tournament, related_name='tournament_invitation_set', on_delete=models.CASCADE)
	from_player = models.ForeignKey(
		'Player', 
		related_name='invitation_sent', 
		on_delete=models.CASCADE
	)
	to_player = models.ForeignKey(
		'Player', 
		related_name='invitation_received', 
		on_delete=models.CASCADE
	)
	created_at = models.DateTimeField(auto_now_add=True)
	is_confirmed = models.BooleanField(default=False)
	