from rest_framework import viewsets, permissions, status
from .models import Player, Tournament, PlayerStatistics, TournamentInvitation
from .serializers import PlayerSerializer, TournamentSerializer, PlayerStatisticsSerializer, TournamentInvitationSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsInvitedRecipientOrAdmin
from server_side_pong.serializers import GameSerializer
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.apps import apps
from rest_framework.pagination import PageNumberPagination
from server_side_pong.models import Game
from django.db.models import Q
from urllib.parse import urlparse

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.info()

class PlayerRankingPagination(PageNumberPagination):
	page_size = 10


class PlayerViewSet(viewsets.ModelViewSet):
	queryset = Player.objects.all()
	serializer_class = PlayerSerializer
	permission_classes = [permissions.IsAuthenticated]

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

	http_method_names = ['get', 'post', 'head', 'options']

class HistoryViewSet(viewsets.ViewSet):
	permission_classes = [permissions.IsAuthenticated]

	def list(self, request, player_id=None, history_type=None):
		self.Game = apps.get_model('server_side_pong', 'Game')
		try:
			player = Player.objects.get(id=player_id)
		except Player.DoesNotExist:
			return Response({"detail": "Player not found."}, status=404)

		if history_type == "matches":
			history = player.match_history
			valid_statuses = dict(self.Game.STATUS_CHOICES)
			serializer_class = GameSerializer
		elif history_type == "tournaments":
			history = player.tournament_history
			valid_statuses = dict(Tournament.STATUS_CHOICES)
			serializer_class = TournamentSerializer
		else:
			return Response({"detail": "Invalid history type."}, status=400)

		status_filter = self.request.query_params.get('status', None)
		if status_filter:
			status_list = status_filter.split(',')
			invalid_statuses = [status for status in status_list if status not in valid_statuses]
			if invalid_statuses:
				return Response({"detail": f"Invalid status: {', '.join(invalid_statuses)}."}, status=400)
			history = history.filter(status__in=status_list)
		logging.info(f"history back {history_type} : {history}")
		serializer = serializer_class(history, many=True)
		return Response(serializer.data)



class TournamentViewSet(viewsets.ModelViewSet):
	serializer_class = TournamentSerializer
	permission_classes = [permissions.IsAuthenticated]
	http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

	def get_queryset(self):
		queryset = Tournament.objects.all()

		status_filter = self.request.query_params.get('status', None)
		if status_filter:
			status_list = status_filter.split(',')
			invalid_statuses = [status for status in status_list if status not in dict(Tournament.STATUS_CHOICES)]
			if invalid_statuses:
				raise ValidationError({"detail": f"Invalid status: {', '.join(invalid_statuses)}. Must be one of: {', '.join(dict(Tournament.STATUS_CHOICES).keys())}."})
			queryset = queryset.filter(status__in=status_list)

		return queryset
	
	def _check_active_game(self, player):
		"""Check if player already in an active game"""
		logging.info(f"Check if in game : {player}")
		active_game = Game.objects.filter(
            (Q(player1=player) | Q(player2=player) | Q(created_by=player)) &
            ~Q(status__in=['completed', 'interrupted'])
        ).first()
		if active_game:
			raise PermissionDenied({"detail": "You are not allowed to create/join a new tournament while you are in an active game."})

	def _check_tournament_constraints(self, player, tournament_id):
		"""Checks if the player is in an active tournament and if another tournament is created within the tournament"""
		logging.info(f"Check if in tournament : {player}")
		logging.info(f"tournament id : {tournament_id}")
		active_tournament = Tournament.objects.filter(
            participants=player,
            status__in=['upcoming', 'ongoing']
        ).first()
		
		if active_tournament and active_tournament != None:
			logging.info(f"active tournament : {tournament_id}")
			if not tournament_id or int(tournament_id) != active_tournament.id:
				raise PermissionDenied({"detail": "You are not allowed to create/join a tournament while you are in an active tournament."})

	def create(self, request, *args, **kwargs):
		user = request.user
		player = user.player_profile
		tournament_id = request.data.get('tournament')
        
        # check constraints  of ahother game or tournament
		self._check_active_game(player)
		self._check_tournament_constraints(player, tournament_id)

		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)

		return Response(serializer.data, status=status.HTTP_201_CREATED)
	
	def perform_create(self, serializer):
		tournament = serializer.save(created_by=self.request.user.player_profile)
		tournament.participants.add(self.request.user.player_profile)

	@action(detail=True, methods=['post'])
	def join(self, request, pk=None):
		tournament = self.get_object()
		player = request.user.player_profile

        # check constraints  of ahother game or tournament
		self._check_active_game(player)
		self._check_tournament_constraints(player, tournament.id)
		
		if tournament.participants.filter(id=player.id).exists():
			return Response({"detail": "You're already a participant to this tournament."}, status=status.HTTP_400_BAD_REQUEST)
		if tournament.max_players and tournament.participants.count() >= tournament.max_players:
			return Response({"detail": "The tournament is already full."}, status=status.HTTP_400_BAD_REQUEST)
		if tournament.status != 'upcoming':
			return Response({"detail": "The tournament has already began."}, status=status.HTTP_400_BAD_REQUEST)
		tournament.participants.add(player)
		return Response({"detail": "You're registered for this tournament."}, status=status.HTTP_200_OK)
	
	@action(detail=True, methods=['post'])
	def withdraw(self, request, pk=None):
		tournament = self.get_object()
		player = request.user.player_profile
		if not tournament.participants.filter(id=player.id).exists():
			return Response({"detail": "You need to be a participant in order to withdraw."}, status=status.HTTP_400_BAD_REQUEST)
		if tournament.status != 'upcoming':
			return Response({"detail": "The tournament has already began."}, status=status.HTTP_400_BAD_REQUEST)
		tournament.participants.remove(player)
		return Response({"detail": "You withdraw from this tournament."}, status=status.HTTP_200_OK)

	
	@action(detail=True, methods=['post'])
	def invite(self, request, pk=None):
		tournament = self.get_object()
		host = request.user.player
		player_id = request.data.get('player_id')
		to_invite = Player.objects.get(id=player_id)

		if not (tournament.participants.filter(id=host.id).exists() or host.user.is_superuser):
			return Response({"detail": "You must be a participant or admin to invite a player."}, status=status.HTTP_400_BAD_REQUEST)
		if tournament.participants.filter(id=to_invite.id).exists():
			return Response({"detail": "Player already a participant."}, status=status.HTTP_400_BAD_REQUEST)
		if tournament.max_players and tournament.participants.count() >= tournament.max_players:
			return Response({"detail": "Tournament is already full."}, status=status.HTTP_400_BAD_REQUEST)
		if tournament.status != 'upcoming':
			return Response({"detail": "The tournament has already began."}, status=status.HTTP_400_BAD_REQUEST)
		TournamentInvitation.objects.create(from_player=host, to_user=to_invite)
		

	@action(detail=True, methods=['post'])
	def start_tournament(self, request, pk=None):
		tournament = self.get_object()
		
		if tournament.status != 'upcoming':
			return Response({"detail": "Tournament cannot start."}, status=status.HTTP_400_BAD_REQUEST)
		if tournament.participants.count() < 2:
			return Response({"detail": "Not enough participant for the tournament to start."}, status=status.HTTP_400_BAD_REQUEST)
		
		tournament.generate_initial_matches(tournament)

		return Response({"detail": "Tournament has started."}, status=status.HTTP_200_OK)

class PlayerStatisticsViewSet(viewsets.ViewSet):
	permission_classes = [permissions.IsAuthenticated]

	def list(self, request):
		player_statistics = PlayerStatistics.objects.filter(player=request.user.player_profile).first()

		if not player_statistics:
			return Response({"detail": "Statistics not found for the current player."}, status=404)

		serializer = PlayerStatisticsSerializer(player_statistics)
		return Response(serializer.data)
	
	def retrieve(self, request, pk=None):
		try:
			if (not pk.isdigit()):
				raise NotFound({"detail": "Numeric value expected for id."})
			player_stats = PlayerStatistics.objects.get(player_id=pk)
		except PlayerStatistics.DoesNotExist:
			return Response({"detail": "Statistics not found for this player."}, status=404)

		serializer = PlayerStatisticsSerializer(player_stats)
		return Response(serializer.data)
	

class PlayerRankingViewSet(viewsets.ViewSet):
	permission_classes = [permissions.IsAuthenticated]

	def list(self, request):
		players = Player.objects.get_ranked_players()
		data = [
			{
				"player_id": player.id,
				"player_avatar_url": self.process_avatar_url(player.avatar.url),
				"player_username": player.user.username,
				"player_nickname": player.nickname,
				"win_ratio": round(player.win_ratio * 100, 2),  # Format en pourcentage
				"matches_played": player.stats.matches_played,
				"matches_won": player.stats.matches_won
			}
			for player in players if player.stats.matches_played > 0  # Ignorer les joueurs sans stats
		]
		return Response(data)
	
	@staticmethod
	def process_avatar_url(avatar_url):
		parsed_url = urlparse(avatar_url)
		avatar_path = parsed_url.path  # Remove the scheme and netloc (domain + port)
		if avatar_path.startswith('/media/https%3A/'):
			avatar_path = avatar_path.replace('/media/https%3A/', 'https://')
		return avatar_path
	

class TournamentInvitationViewSet(viewsets.ModelViewSet):
	queryset = TournamentInvitation.objects.select_related('from_player', 'to_player').all()
	serializer_class = TournamentInvitationSerializer
	permission_classes = [permissions.IsAuthenticated]
	http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

	def perform_create(self, serializer):
		current_user = self.request.user
		from_player = current_user.player_profile
		to_player = serializer.validated_data['to_player']
		tournament = serializer.validated_data['tournament']

		if TournamentInvitation.objects.filter(
			tournament=tournament,
			from_player=from_player,
			to_player=to_player
		).exists():
			raise ValidationError({"detail":"This player has already been invited to the tournament."})

		if not (tournament.participants.filter(id=from_player.id).exists() or current_user.is_superuser):
			raise ValidationError({"detail":"You must be a participant or an admin to invite players."})
			
		if tournament.status != 'upcoming':
			raise ValidationError({"detail":"The tournament has already started."})
		
		if tournament.participants.count() >= tournament.max_players:
			raise ValidationError({"detail":"The tournament is already full."})
		
		if tournament.participants.filter(id=to_player.id).exists():
			raise ValidationError({"detail":"The player is already a participant."})
		serializer.save(from_player=from_player,  is_confirmed=False)

	@action(detail=True, methods=['put'], permission_classes=[IsInvitedRecipientOrAdmin])
	def accept_invitation(self, request, pk=None):
		invitation = self.get_object()
		if invitation.is_confirmed:
			return Response({"detail": "You already accepted this invitation."}, status=status.HTTP_400_BAD_REQUEST)
		invitation.is_confirmed = True
		invitation.save()
		tournament = invitation.tournament
		tournament.participants.add(invitation.to_player)
		return Response({"detail": "You are now a participant of this tournament."}, status=status.HTTP_200_OK)
	
	@action(detail=True, methods=['put'], permission_classes=[IsInvitedRecipientOrAdmin])
	def refuse_invitation(self, request, pk=None):
		invitation = self.get_object()
		if invitation.is_confirmed:
			return Response({"detail": "You already accepted this invitation."}, status=status.HTTP_400_BAD_REQUEST)
		invitation.delete()
		return Response({"detail": "You declined this invitation"}, status=status.HTTP_200_OK)
