import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from rest_framework.test import APIClient
from rest_framework import status
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from hello_django.asgi import application
from server_side_pong.models import Game
from matchmaking.models import Player
from users.models import CustomUser
from server_side_pong.consumers.consumers import GameManager
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def authenticate(client, username, password):
    """Authenticate a user and set up cookies with JWT tokens."""
    # Reset cookies and credentials
    client.cookies.clear()  # Clears all cookies
    client.credentials()    # Removes previous Authorization header

    login_url = reverse('login-user')
    response = client.post(login_url, {'username': username, 'password': password}, format='json')
    
    # Vérifier que la connexion a réussi
    assert response.status_code == status.HTTP_200_OK, f"Login failed: {response.content}"
    
    # Extraire les tokens des cookies
    access_token = response.cookies.get('access').value
    refresh_token = response.cookies.get('refresh').value
    
    # S'assurer que les tokens existent
    assert access_token is not None, "Access token not found in cookies."
    assert refresh_token is not None, "Refresh token not found in cookies."

     # Set the cookies in the client
    client.cookies['access'] = access_token
    client.cookies['refresh'] = refresh_token
    

PADDLE_SPEED = 5
BALL_SPEED = 5
BALL_RADIUS = 10
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_HEIGHT = 100
ROUND_NEEDED = 5

def get_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)

@pytest.mark.asyncio
@pytest.mark.django_db
class TestPongConsumer:
    @pytest_asyncio.fixture
    async def setup_game(self):
        # Create test users
        self.user1 = await sync_to_async(CustomUser.objects.create_user)(
            username="Johnny", email="player1@example.com", password="Password1"
        )
        self.user2 = await sync_to_async(CustomUser.objects.create_user)(
            username="Freddy", email="player2@example.com", password="Password2"
        )

        # Generate a JWT token for a user

        # In your test setup
        self.access_token1, self.refresh_token1 =  await get_jwt_token(self.user1)
        self.access_token2, self.refresh_token2 =  await get_jwt_token(self.user2)

        # print(f"User1: {self.user1}, Player1: {player}") Async issue
        # print(f"User2: {self.user2}, Player2: {self.player2}")
        # print(f"Game ID: {self.game.id}")


        # Create a game instance
        self.game = await sync_to_async(Game.objects.create)(
            rounds_needed=5, game_type="remote"
        )

        return {
            "game_id": self.game.id,
            "token1": self.token1.key,
            "token2": self.token2.key,
        }

    async def test_remote_game_init_and_join(self, setup_game):
        # First player (creator) connects
        GameManager.create_game(game_id=setup_game['game_id'])

        communicator1 = WebsocketCommunicator(
            application,
            f"/ws/server_side_pong/remote/{setup_game['game_id']}/",
        )
        communicator1.scope["user"] = self.user1

        communicator2 = WebsocketCommunicator(
            application,
            f"/ws/server_side_pong/remote/{setup_game['game_id']}/",
        )
        communicator2.scope["user"] = self.user2

        # Debug: Check user and game setup
        print(f"User1: {self.user1}, User2: {self.user2}")
        print(f"GameManager.games: {GameManager.games}")

        # Connect the first player
        connected1, _ = await communicator1.connect()
        assert connected1

        # Connect the second player
        connected2, _ = await communicator2.connect()
        assert connected2

        response1 = await communicator1.receive_json_from()
        assert response1["type"] == "role_assignment"
        assert response1["role"] == "player1"    

        response2 = await communicator2.receive_json_from()
        assert response1["type"] == "role_assignment"
        assert response2["role"] ==  "player2"

        response3 = await communicator1.receive_json_from()
        assert response3["ball"]
        assert response3["players"]["player1"]["x"] == 10
        assert response3["scores"]["player1"] == 0

        response4 = await communicator2.receive_json_from()
        assert response4["ball"]
        assert response4["players"]["player1"]["x"] == 10
        assert response4["scores"]["player1"] == 0

        response5 = await communicator1.receive_json_from()
        assert response5["ball"]
        assert response5["players"]["player1"]["x"] == 10
        assert response5["scores"]["player1"] == 0

        response6 = await communicator2.receive_json_from()
        assert response6["ball"]["x"] == 410 #moved
        assert response6["players"]["player1"]["x"] == 10
        assert response6["players"]["player1"]["y"] == 250
        assert response6["scores"]["player1"] == 0

        # Simulate game logic or actions
        await communicator1.send_json_to({"type": "gameplay", "movement": "up"})
        response7 = await communicator1.receive_json_from()
        response7 = await communicator1.receive_json_from()
        response7 = await communicator1.receive_json_from()
        assert response7["players"]["player1"]["x"] == 10
        assert response7["players"]["player1"]["y"] == 245

        # Disconnect both players
        await communicator1.disconnect()
        await communicator2.disconnect()


User = get_user_model()

async def test_websocket_connection():
    # Create users and tokens
    user1 = await sync_to_async(User.objects.create_user)(username="user1", password="password1")
    access_token1, _ = await get_jwt_token(user1)
    
    # Mock the WebSocket headers
    headers = [
        (b"cookie", f"access={access_token1}; Path=/; HttpOnly".encode())
    ]

    # Create a WebSocket communicator
    communicator = WebsocketCommunicator(application, "/ws/some-path/", headers=headers)
    connected, subprotocol = await communicator.connect()
    
    assert connected

    # Close the connection
    await communicator.disconnect()

@pytest.mark.django_db
class TestGameViewSet:
    @pytest.fixture
    def setup_user(db):
        """Create a fake authenticated user."""
        user = CustomUser.objects.create_user(
            username="TestUser",
            email="testuser@example.com",
            password="TestPassword1",
        )
        return user

    @pytest.fixture
    def client_with_auth(db, setup_user):
        """Create a test client with JWT authentication."""
        # Generate a JWT token for the user
        refresh = RefreshToken.for_user(setup_user)
        access_token = str(refresh.access_token)

        # Create a test client and add the JWT token to the headers
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return client

    def test_create_local_game(self, client_with_auth):
        response = client_with_auth.post(
            "/api/games/",
            data={"rounds_needed": 3, "game_type": "local"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert "game_id" in data
        assert data["status"] == "waiting"
        assert data["message"] == "Local game created"

    def test_create_remote_game(self, client_with_auth):
        response = client_with_auth.post(
            "/api/games/",
            data={"rounds_needed": 5, "game_type": "remote"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert "game_id" in data
        assert data["status"] == "waiting"
        assert data["message"] == "Remote game created"

    def test_create_game_invalid_rounds(self, client_with_auth):
        response = client_with_auth.post(
            "/api/games/",
            data={"rounds_needed": 0, "game_type": "local"},
            format="json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "rounds_needed" in data
        assert data["rounds_needed"] == ["Rounds needed must be at least 1."]

    def test_create_game_invalid_type(self, client_with_auth):
        response = client_with_auth.post(
            "/api/games/",
            data={"rounds_needed": 3, "game_type": "invalid_type"},
            format="json",
        )
        assert response.status_code == 400




from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from matchmaking.models import Tournament
from server_side_pong.models import Game
from django.utils import timezone
from datetime import timedelta


class GameCreationTests(APITestCase):
    
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123', email='user1@a.com')
        
        authenticate(self.client, username='alice', password='password123')
        
        self.player1 = self.user1.player_profile
        
        # URL for game creation
        self.create_game_url = reverse('game-list')  # Assurez-vous que c'est la bonne URL

        # Base game data
        self.game_data = {
            'name': 'MyTestGame',
            'game_type': 'remote',
            'rounds_needed': 3,
        }


    def test_create_game_when_no_active_game(self):
        """Test qu'un joueur peut créer une game quand il n'a pas de partie active"""
        response = self.client.post(self.create_game_url, self.game_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Game.objects.count(), 1)

    def test_create_game_with_active_game(self):
        """Test qu'un joueur ne peut pas créer une game s'il a déjà une partie active"""
        # Create an active game first
        Game.objects.create(
            player1=self.player1,
            status='ongoing',
            game_type='remote',
            rounds_needed=3
        )

        response = self.client.post(self.create_game_url, self.game_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Game.objects.count(), 1)

    def test_create_tournament_game_when_in_tournament(self):
        """Test qu'un joueur peut créer une game de tournoi quand il est dans ce tournoi"""
        # Create tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            start_time=timezone.now() + timedelta(days=1),
            status='ongoing'
        )
        tournament.participants.add(self.player1)

        # Try to create a game for this tournament
        tournament_game_data = {
            **self.game_data,
            'tournament': tournament.id
        }
        response = self.client.post(self.create_game_url, tournament_game_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_non_tournament_game_when_in_tournament(self):
        """Test qu'un joueur ne peut pas créer une game hors tournoi quand il est dans un tournoi"""
        # Create and add player to tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            start_time=timezone.now() + timedelta(days=1),
            status='ongoing'
        )
        tournament.participants.add(self.player1)

        # Try to create a non-tournament game
        response = self.client.post(self.create_game_url, self.game_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_game_for_different_tournament(self):
        """Test qu'un joueur ne peut pas créer une game pour un autre tournoi que le sien"""
        # Create two tournaments
        tournament1 = Tournament.objects.create(
            name='Tournament 1',
            start_time=timezone.now() + timedelta(days=1),
            status='ongoing'
        )
        tournament2 = Tournament.objects.create(
            name='Tournament 2',
            start_time=timezone.now() + timedelta(days=1),
            status='ongoing'
        )
        tournament1.participants.add(self.player1)

        # Try to create a game for tournament2
        wrong_tournament_game_data = {
            **self.game_data,
            'tournament': tournament2.id
        }
        response = self.client.post(self.create_game_url, wrong_tournament_game_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_game_with_completed_game(self):
        """Test qu'un joueur peut créer une nouvelle game si sa précédente est terminée"""
        # Create a completed game
        Game.objects.create(
            player1=self.player1,
            status='completed',
            game_type='remote',
            rounds_needed=3
        )

        response = self.client.post(self.create_game_url, self.game_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Game.objects.count(), 2)

    def test_create_game_invalid_game_type(self):
        """Test la validation du type de jeu"""
        invalid_game_data = {
            **self.game_data,
            'game_type': 'invalid_type'
        }
        response = self.client.post(self.create_game_url, invalid_game_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
