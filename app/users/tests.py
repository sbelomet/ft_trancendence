from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from .models import Friendship
from matchmaking.models import PlayerStatistics, Tournament
from rest_framework.test import APIClient
from server_side_pong.models import Game
from django.utils import timezone
from unittest import mock
from matchmaking.serializers import PlayerStatisticsSerializer


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
    
    # Définir les tokens dans les en-têtes pour les requêtes suivantes
    #client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')




class CustomUserModelTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123', email='user1@a.com')
        self.user2 = User.objects.create_user(username='bob', password='password123', email='user2@a.com')
        self.user3 = User.objects.create_user(username='charlie', password='password123', email='user3@a.com')

    def test_user_creation(self):
        """Test la création des utilisateurs"""
        self.assertEqual(self.user1.username, 'alice')
        self.assertEqual(self.user2.username, 'bob')
        self.assertEqual(self.user3.username, 'charlie')
        self.assertTrue(self.user1.check_password('password123'))
        self.assertTrue(self.user2.check_password('password123'))

    def test_user_str_method(self):
        """Test la méthode __str__ des utilisateurs"""
        self.assertEqual(str(self.user1), 'alice')
        self.assertEqual(str(self.user2), 'bob')


class FriendshipAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123', email='user1@a.com')
        self.user2 = User.objects.create_user(username='bob', password='password123', email='user2@a.com')
        self.user3 = User.objects.create_user(username='charlie', password='password123', email='user3@a.com')
        self.user4 = User.objects.create_user(username='Jules', password='password123', email='user4@a.com')

        # Authentifier le client en tant qu'alice
        authenticate(self.client, username='alice', password='password123')

    def test_send_friend_request(self):
        """Test l'envoi d'une demande d'amitié"""
        authenticate(self.client, username='alice', password='password123')
        url = reverse('friendship-list')
        data = {'to_user': self.user2.id}
        response = self.client.post(url, data, format='json')
        #print("Response data:", response.data)
        #print("Status code:", response.status_code)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Friendship.objects.count(), 1)
    
    def test_send_blocked_request(self):
        """Test l'envoi d'une demande d'amitié"""
        authenticate(self.client, username='alice', password='password123')
        url = reverse('friendship-list')
        data = {'to_user': self.user4.id}
        response = self.client.post(url, data, format='json')
        #print("Response data:", response.data)
        #print("Status code:", response.status_code)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Friendship.objects.count(), 1)

    def test_confirm_friend_request(self):
        """Test que seul le destinataire peut confirmer une demande d'amitié"""
        # Clients pour chaque utilisateur
        client_alice = APIClient()
        client_bob = APIClient()
        client_charlie = APIClient()

        # Alice envoie une demande d'amitié à Bob
        authenticate(client_alice, username='alice', password='password123')
        url = reverse('friendship-list')
        data = {'to_user': self.user2.id}  # Bob
        response = client_alice.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        friendship = Friendship.objects.get(from_user=self.user1, to_user=self.user2)

        # Alice tente d'accepter la demande (devrait échouer)
        authenticate(client_alice, username='alice', password='password123')
        url = reverse('friendship-accept-friendship', args=[friendship.id])
        response = client_alice.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Bob accepte la demande
        authenticate(client_bob, username='bob', password='password123')
        url = reverse('friendship-accept-friendship', args=[friendship.id])
        response = client_bob.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        friendship.refresh_from_db()
        self.assertTrue(friendship.has_rights)

        # Charlie tente d'accepter la demande (devrait échouer)
        authenticate(client_charlie, username='charlie', password='password123')
        url = rurl = reverse('friendship-accept-friendship', args=[friendship.id])
        response = client_charlie.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_prevent_duplicate_friendships(self):
        """Test qu'une amitié dupliquée ne peut pas être créée"""
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        url = reverse('friendship-list')
        data = {'to_user': self.user2.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_friend_self(self):
        """Test qu'un utilisateur ne peut pas s'ajouter lui-même comme ami via l'API"""
        url = reverse('friendship-list')
        data = {'to_user': self.user1.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserAPITest(APITestCase):
    def test_create_user(self):
        """Test la création d'un utilisateur via l'API"""
        url = reverse('register')
        data = {
            'username': 'david',
            'email': 'david@example.com',
            'password': 'securepassword123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='david')
        self.assertTrue(user.check_password('securepassword123'))
        self.assertNotIn('password', response.data)
        response_data = response.json()
        self.assertEqual(response_data.get('redirect_url'), '/login/')

    def test_login_user(self):
        """Test user login and JWT token in cookies"""
        user = User.objects.create_user(username='eve', password='password123', email='eve@example.com')
        login_url = reverse('login-user')
        response = self.client.post(login_url, {'username': 'eve', 'password': 'password123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Ensure JWT tokens are stored in cookies
        self.assertIn('access', response.cookies)

    def test_authenticated_endpoint(self):
        """Test accessing an authenticated endpoint with JWT in cookies"""
        user = User.objects.create_user(username='eve', password='password123', email='eve@example.com')
        authenticate(self.client, username='eve', password='password123')

        # Access a protected endpoint
        protected_url = reverse('midtest')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_logout_user(self):
        """Test if the user can successfully log out"""
        # Log in user first
        user = User.objects.create_user(username='eve', password='password123', email='eve@example.com')
        login_url = reverse('login-user')
        response = self.client.post(login_url, {'username': 'eve', 'password': 'password123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Ensure tokens are in cookies
        self.assertIn('access', response.cookies)
        self.assertIn('refresh', response.cookies)
        
		# Authenticate with cookies for subsequent requests
        self.client.cookies['access'] = response.cookies['access'].value
        self.client.cookies['refresh'] = response.cookies['refresh'].value
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.cookies['access'].value}")

        # Log out user
        logout_url = reverse('logout-user')
        logout_response = self.client.post(logout_url)
        
        # Ensure logout succeeds
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)
        
		# Verify the redirection to the login page
        response_data = logout_response.json()
        self.assertEqual(response_data.get('redirect_url'), '/pre_login/')

        # Verify cookies are cleared
        self.assertIn('access', logout_response.cookies)
        self.assertIn('refresh', logout_response.cookies)
        self.assertEqual(logout_response.cookies['access'].value, '')
        self.assertEqual(logout_response.cookies['refresh'].value, '')
        
        self.client.cookies.clear()
        self.client.credentials(HTTP_AUTHORIZATION=None)

        # Attempt to access a protected endpoint post logout
        protected_url = reverse('midtest')
        response = self.client.get(protected_url)
        
        # Ensure access fails because the user is logged out
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123', email='alice@example.com')
        self.user2 = User.objects.create_user(username='bob', password='password123', email='bob@example.com')

    def test_only_friends_can_see_friends(self):
        """Test que seul un ami peut voir les amis d'un utilisateur"""
        authenticate(self.client, username='alice', password='password123')

        # Tenter de voir les amis de user2 (ils ne sont pas encore amis)
        url = reverse('user-see-friend-friends', args=[self.user2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Créer une amitié confirmée entre user1 et user2
        friendship = Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        authenticate(self.client, username='bob', password='password123')
        url = reverse('friendship-detail', args=[friendship.id])
        data = {'has_rights': True}
        response = self.client.patch(url, data, format='json')
        #print("Response data:", response.data)
        #print("Status code:", response.status_code)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        friendship.refresh_from_db()
        self.assertTrue(friendship.has_rights)
        authenticate(self.client, username='alice', password='password123')
        url = reverse('user-see-friend-friends', args=[self.user2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refuse_friend_request(self):
        """Test que seul le destinataire peut refuser une demande d'amitié"""
        # Clients pour chaque utilisateur
        client_alice = APIClient()
        client_bob = APIClient()

        # Alice envoie une demande d'amitié à Bob
        authenticate(client_alice, username='alice', password='password123')
        url = reverse('friendship-list')
        data = {'to_user': self.user2.id}
        response = client_alice.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        friendship = Friendship.objects.get(from_user=self.user1, to_user=self.user2)

        # Alice tente de refuser la demande (devrait échouer)
        authenticate(client_alice, username='alice', password='password123')
        url = reverse('friendship-refuse-friendship', args=[friendship.id])
        response = client_alice.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Bob refuse la demande
        authenticate(client_bob, username='bob', password='password123')
        url = reverse('friendship-refuse-friendship', args=[friendship.id])
        response = client_bob.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Friendship.objects.filter(id=friendship.id).exists())


class UserSignalsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')

    def test_user_login_updates_is_online(self):
        """Test que l'utilisateur est marqué en ligne après la connexion"""
        authenticate(self.client, username='testuser', password='testpassword')
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_online)

    def test_user_logout_updates_is_online(self):
        """Test que l'utilisateur est marqué hors ligne après la déconnexion"""
        # Authenticate the user
        authenticate(self.client, username='testuser', password='testpassword')

        # Perform logout
        logout_url = reverse('logout-user')
        response = self.client.post(logout_url, format='json')
        
        # Ensure the logout was successful
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        
        # Verify the user is marked offline
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_online)

class UserUpdatePermissionTest(APITestCase):
    def setUp(self):
        # Create two users
        self.user1 = User.objects.create_user(username='user1', password='password123', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', password='password123', email='user2@example.com')

        # Profile update URL for each user
        self.user1_update_url = reverse('user-detail', args=[self.user1.id])
        self.user2_update_url = reverse('user-detail', args=[self.user2.id])

        # Initialize API clients
        self.client_user1 = APIClient()
        self.client_user2 = APIClient()

    def test_user_can_update_own_profile(self):
        """Test that a user can update their own profile"""
        authenticate(self.client_user1, username='user1', password='password123')
        data = {'username': 'new_user1', 'email': 'new_user1@example.com'}
        response = self.client_user1.patch(self.user1_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'new_user1')
        self.assertEqual(self.user1.email, 'new_user1@example.com')

    def test_user_cannot_update_another_users_profile(self):
        """Test that a user cannot update another user's profile"""
        authenticate(self.client_user1, username='user1', password='password123')
        data = {'username': 'hacked_user2', 'email': 'hacked_user2@example.com'}
        response = self.client_user1.patch(self.user2_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user2.refresh_from_db()
        self.assertNotEqual(self.user2.username, 'hacked_user2')
        self.assertNotEqual(self.user2.email, 'hacked_user2@example.com')

    def test_unauthenticated_user_cannot_update_any_profile(self):
        """Test that an unauthenticated user cannot update any profile"""
        data = {'username': 'unauth_user1', 'email': 'unauth_user1@example.com'}
        response = self.client.patch(self.user1_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch(self.user2_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class MatchHistoryAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='alice', password='password123', email='alice@example.com'
        )
        self.user2 = User.objects.create_user(
            username='bob', password='password123', email='bob@example.com'
        )
        self.client1 = APIClient()
        self.client2 = APIClient()
        authenticate(self.client1, username='alice', password='password123')
        authenticate(self.client2, username='bob', password='password123')
        self.player1 = self.user1.player_profile
        self.player2 = self.user2.player_profile

    def test_match_history_update_on_game_creation(self):
        """Test que le match_history est mis à jour après la création d'un jeu."""
        game = Game.objects.create(
            player1=self.player1,
            player2=self.player2,
            rounds_needed=3,
            start_time=timezone.now(),
            status='completed',
            winner=self.player2
        )


        # Vérifier que le match est dans l'historique des deux joueurs
        self.assertIn(game, self.player1.match_history)
        self.assertIn(game, self.player2.match_history)

        # Vérifier que le gagnant est bien défini
        self.assertEqual(game.winner, self.player2)



    def test_player_statistics_serialization(self):
        """Test que les statistiques sont correctement sérialisées."""
        # Créer un jeu complet pour générer des statistiques
        game = Game.objects.create(
            player1=self.player1,
            player2=self.player2,
            rounds_needed=3,
            start_time=timezone.now(),
            status='completed',
            winner=self.player1
        )

        # GamePlayer.objects.create(game=game, player=self.user1.player_profile, score=15, position=1)
        # GamePlayer.objects.create(game=game, player=self.user2.player_profile, score=10, position=2)

        # Récupérer ou créer les statistiques pour user1
        stats, _ = PlayerStatistics.objects.get_or_create(player=self.user1.player_profile)

        # Récupérer les détails de user1
        url = reverse('user-detail', args=[self.user1.id])
        response = self.client1.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que les statistiques sont présentes et correctes
        stats_data = response.data.get('stats', {})
        self.assertEqual(stats_data['matches_played'], 1)
        self.assertEqual(stats_data['matches_won'], 1)
        # self.assertEqual(stats_data['total_points'], 15)
        self.assertEqual(stats_data['win_rate'], 100.0)
        # self.assertEqual(stats_data['average_score'], 15.0)



class PlayerStatisticsAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='alice', password='password123', email='alice@example.com'
        )
        self.user2 = User.objects.create_user(
            username='bob', password='password123', email='bob@example.com'
        )
        self.player1 = self.user1.player_profile 
        self.player2 = self.user2.player_profile  
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)


    def test_player_statistics_update_on_game_creation(self):
        """Test que les statistiques sont mises à jour après un jeu."""
        game = Game.objects.create(
            player1=self.player1,
            player2=self.player2,
            rounds_needed=3,
            start_time=timezone.now(),
            status='completed',
            winner=self.player1
        )


        # Récupérer les statistiques pour player1
        stats = PlayerStatistics.objects.get(player=self.player1)

        # Vérifier les statistiques calculées
        self.assertEqual(stats.matches_played, 1)
        self.assertEqual(stats.matches_won, 1)
        self.assertEqual(stats.win_rate, 100.0)

        # Récupérer les statistiques pour player2
        stats_player2 = PlayerStatistics.objects.get(player=self.player2)
        self.assertEqual(stats_player2.matches_played, 1)
        self.assertEqual(stats_player2.matches_won, 0)
        self.assertEqual(stats_player2.win_rate, 0.0)



def test_player_statistics_serialization(self):
    """Test que les statistiques sont correctement sérialisées."""
    # Créer plusieurs matchs
    matches_won = 0
    for i in range(5):
        winner = self.player1 if i % 2 == 0 else self.player2  # Alternance des gagnants
        Game.objects.create(
            rounds_needed=3,
            start_time=timezone.now(),
            status='completed',
            winner=winner
        )
        if winner == self.player1:
            matches_won += 1

def test_tournament_statistics_update(self):
    """Test que les statistiques des joueurs sont mises à jour après un tournoi."""
    # Créer un tournoi
    tournament = Tournament.objects.create(
        name="Test Tournament",
        start_time=timezone.now(),
        status="completed",
        winner=self.player1,
    )

    # Créer des matchs dans le tournoi
    for _ in range(3):
        Game.objects.create(
            tournament=tournament,
            rounds_needed=3,
            start_time=timezone.now(),
            status='completed',
            winner=self.player1,
        )

    # Récupérer les statistiques pour player1
    stats = PlayerStatistics.objects.get(player=self.player1)

    # Vérifier les statistiques calculées
    self.assertEqual(stats.matches_played, 3)
    self.assertEqual(stats.matches_won, 3)
    self.assertEqual(stats.win_rate, 100.0)


    # Récupérer les statistiques pour player1
    stats = PlayerStatistics.objects.get(player=self.player1)

    # Sérialiser les statistiques
    serializer = PlayerStatisticsSerializer(stats)
    stats_data = serializer.data

    # Vérifier les statistiques sérialisées
    self.assertEqual(stats_data['matches_played'], 5)
    self.assertEqual(stats_data['matches_won'], matches_won)
    self.assertEqual(stats_data['win_rate'], (matches_won / 5) * 100)



class CompleteOAuth2FlowTest(APITestCase):
    @mock.patch('users.views.requests.post')
    @mock.patch('users.views.requests.get')
    def test_complete_oauth2_flow(self, mock_get, mock_post):
        """Test the complete OAuth2 flow."""
        # Mock the token exchange
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'fake_access_token',
            'refresh_token': 'fake_refresh_token',
            'expires_in': 3600,
            'token_type': 'Bearer',
            'scope': 'public',
        }

        # Mock retrieving user info
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': 123456,
            'login': 'testuser',
            'email': 'testuser@42.fr',
            'image_url': 'http://example.com/avatar.jpg',
        }

        # Simulate state in session
        session = self.client.session
        session['oauth_state'] = 'random_state_string'
        session.save()

        # Simulate the callback with a valid code and state
        callback_url = reverse('oauth-callback')
        response = self.client.get(
            callback_url,
            {'code': 'valid_code', 'state': 'random_state_string'}
        )

        # Verify the redirection to the home page
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')

        # Verify the user was created
        user = User.objects.get(email='testuser@42.fr')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.is_online)

        # Verify the tokens in the cookies
        self.assertIn('access', response.cookies)
        self.assertIn('refresh', response.cookies)

