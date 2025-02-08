from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import Game
from .serializers import GameSerializer
from users.models import CustomUser
from server_side_pong.consumers import consumers
from matchmaking.models import Tournament
import socket
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_local_ip():
    try:
        # Connect to an external host to determine the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google DNS server (safe external host)
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        #print(f"Error obtaining IP: {e}")
        return "localhost"  # Fallback to localhost if there's an error

class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  

    def get_queryset(self):
        queryset = Game.objects.all()

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            status_list = status_filter.split(',')
            invalid_statuses = [status for status in status_list if status not in dict(Game.STATUS_CHOICES)]
            if invalid_statuses:
                raise ValidationError({"detail": f"Invalid status: {', '.join(invalid_statuses)}. Must be one of: {', '.join(dict(Game.STATUS_CHOICES).keys())}."})
            queryset = queryset.filter(status__in=status_list)

        return queryset
    
    def _check_active_game(self, player):
        """Checks if the player is already in an active game"""
        active_game = Game.objects.filter(
            (Q(player1=player) | Q(player2=player) | Q(created_by=player)) &
            ~Q(status__in=['completed', 'interrupted'])
        ).first()

        if active_game:
            raise PermissionDenied({"name": "You are not allowed to create a new game while you are in an active game."})

    def _check_tournament_constraints(self, player, tournament_id):
        """Checks if the player is in an active tournament and if the game is created within the tournament"""
        logging.info(f"Check if in tournament (game) : {player}")
        logging.info(f"tournament id (game) : {tournament_id}")
        active_tournament = Tournament.objects.filter(
            participants=player,
            status__in=['upcoming', 'ongoing']
        ).first()

        if active_tournament:
            if not tournament_id or int(tournament_id) != active_tournament.id:
                raise PermissionDenied({"name":"You are not allowed to create a game outside of a tournament while you are in an active tournament."})


    def create(self, request, *args, **kwargs):
        user = request.user
        player = user.player_profile
        tournament_id = request.data.get('tournament')

        # checks constraints
        self._check_active_game(player)
        self._check_tournament_constraints(player, tournament_id)

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        game = serializer.save()
        logger.info(f"Game instance id: {game.id}")
        try:
            consumers.GameManager.create_game(game.id)
        except ValueError as e:
            logger.error(f"Error creating a game instance with game_id: {e}")

        # Access `gametype` from `request.data`
        game_type = request.data.get("game_type")

        # Prepare the response data
        if game_type == "local":
            response_data = {
                "game_id": game.id,
                "status": game.status,
                "game_type" : "local",
                "invite_link": f"wss://{get_local_ip()}:2000/ws/server_side_pong/local/{game.id}/",
                "detail": "Local game created",
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        elif game_type == "remote":
            response_data = {
                "game_id": game.id,
                "status": game.status,
                "game_type" : "remote",
                "invite_link": f"wss://{get_local_ip()}:2000/ws/server_side_pong/remote/{game.id}/",
                "detail": "Remote game created",
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        # If the `gametype` is invalid, return a bad request response
        return Response(
            {"detail": "Invalid game type. Must be 'local' or 'remote'."},
            status=status.HTTP_400_BAD_REQUEST,
        )