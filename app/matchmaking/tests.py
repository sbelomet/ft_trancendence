# matchmaking/tests.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Tournament, Player, TournamentInvitation
from django.utils import timezone
from server_side_pong.models import Game

User = get_user_model()

class TournamentInvitationTests(APITestCase):
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass')
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='user1pass')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='user2pass')
        self.user3 = User.objects.create_user(username='user3', email='user3@example.com', password='user3pass')

        # Create player profiles
        self.admin_player = Player.objects.get(user=self.admin_user)
        self.player1 = Player.objects.get(user=self.user1)
        self.player2 = Player.objects.get(user=self.user2)
        self.player3 = Player.objects.get(user=self.user3)

        # Create a tournament
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            description='A tournament for testing.',
            start_time=timezone.now(),
            status='upcoming',
            created_by=self.player1,
            max_players=3
        )
        self.tournament.participants.add(self.player1)

        # URLs
        self.invitation_list_url = reverse('tournament-invitation-list')
        self.invitation_detail_url = lambda pk: reverse('tournament-invitation-detail', args=[pk])

        # Clients
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        self.client3 = APIClient()
        self.client3.force_authenticate(user=self.user3)

    def test_create_invitation_success(self):
        """
        Test that a tournament creator can successfully invite another player.
        """
        data = {
            'tournament': self.tournament.id,
            'from_player': self.player1.id,
            'to_player': self.player2.id
        }
        response = self.client1.post(self.invitation_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TournamentInvitation.objects.filter(tournament=self.tournament, from_player=self.player1, to_player=self.player2).exists())

    def test_create_invitation_self_invitation(self):
        """
        Test that a user cannot invite themselves to a tournament.
        """
        data = {
            'tournament': self.tournament.id,
            'from_player': self.player1.id,
            'to_player': self.player1.id
        }
        response = self.client1.post(self.invitation_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot invite yourself to the tournament.', response.data['to_player'])

    def test_create_invitation_already_participant(self):
        """
        Test that a user cannot be invited if they are already a participant.
        """
        self.tournament.participants.add(self.player2)
        data = {
            'tournament': self.tournament.id,
            'from_player': self.player1.id,
            'to_player': self.player2.id
        }
        response = self.client1.post(self.invitation_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Player already a participant.', response.data['detail'])

    def test_create_invitation_tournament_full(self):
        """
        Test that no more invitations can be sent if the tournament is full.
        """
        self.tournament.participants.add(self.player2, self.player3)  # Now max_players=3 is reached
        data = {
            'tournament': self.tournament.id,
            'from_player': self.player1.id,
            'to_player': self.admin_player.id
        }
        response = self.client1.post(self.invitation_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('The tournament is already full.', response.data['detail'])

    def test_create_invitation_tournament_started(self):
        """
        Test that invitations cannot be sent if the tournament has already started.
        """
        self.tournament.status = 'ongoing'
        self.tournament.save()
        data = {
            'tournament': self.tournament.id,
            'from_player': self.player1.id,
            'to_player': self.player2.id
        }
        response = self.client1.post(self.invitation_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('The tournament has already began.', response.data['detail'])

    def test_accept_invitation_success(self):
        """
        Test that an invited player can successfully accept an invitation.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        accept_url = reverse('tournament-invitation-accept-invitation', args=[invitation.id])
        response = self.client2.put(accept_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertTrue(invitation.is_confirmed)
        self.assertIn(self.player2, self.tournament.participants.all())

    def test_accept_invitation_non_recipient(self):
        """
        Test that a user who is not the recipient cannot accept an invitation.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        accept_url = reverse('tournament-invitation-accept-invitation', args=[invitation.id])
        response = self.client3.put(accept_url, format='json')  # user3 is not the recipient
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_accept_already_accepted_invitation(self):
        """
        Test that an invitation cannot be accepted more than once.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2, is_confirmed=True)
        accept_url = reverse('tournament-invitation-accept-invitation', args=[invitation.id])
        response = self.client2.put(accept_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You already accepted this invitation.', response.data['detail'])

    def test_refuse_invitation_success(self):
        """
        Test that an invited player can successfully refuse an invitation.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        refuse_url = reverse('tournament-invitation-refuse-invitation', args=[invitation.id])
        response = self.client2.put(refuse_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(TournamentInvitation.objects.filter(id=invitation.id).exists())
        self.assertNotIn(self.player2, self.tournament.participants.all())

    def test_refuse_invitation_non_recipient(self):
        """
        Test that a user who is not the recipient cannot refuse an invitation.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        refuse_url = reverse('tournament-invitation-refuse-invitation', args=[invitation.id])
        response = self.client3.put(refuse_url, format='json')  # user3 is not the recipient
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_refuse_already_accepted_invitation(self):
        """
        Test that an accepted invitation cannot be refused.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2, is_confirmed=True)
        refuse_url = reverse('tournament-invitation-refuse-invitation', args=[invitation.id])
        response = self.client2.put(refuse_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You already accepted this invitation.', response.data['detail'])

    def test_admin_can_accept_any_invitation(self):
        """
        Test that an admin can accept any invitation.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        accept_url = reverse('tournament-invitation-accept-invitation', args=[invitation.id])
        response = self.admin_client.put(accept_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertTrue(invitation.is_confirmed)
        self.assertIn(self.player2, self.tournament.participants.all())

    def test_admin_can_refuse_any_invitation(self):
        """
        Test that an admin can refuse any invitation.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        refuse_url = reverse('tournament-invitation-refuse-invitation', args=[invitation.id])
        response = self.admin_client.put(refuse_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(TournamentInvitation.objects.filter(id=invitation.id).exists())
        self.assertNotIn(self.player2, self.tournament.participants.all())

    def test_invite_nonexistent_player(self):
        """
        Test that inviting a non-existent player returns an error.
        """
        data = {
            'tournament': self.tournament.id,
            'from_player': self.player1.id,
            'to_player': 9999  # Assuming this ID does not exist
        }
        response = self.client1.post(self.invitation_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid pk "9999" - object does not exist.', str(response.data))

    def test_invite_when_user_not_authenticated(self):
        """
        Test that an unauthenticated user cannot send invitations.
        """
        client = APIClient()  # Unauthenticated client
        data = {
            'tournament': self.tournament.id,
            'from_player': self.player1.id,
            'to_player': self.player2.id
        }
        response = client.post(self.invitation_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_accept_invitation_when_user_not_authenticated(self):
        """
        Test that an unauthenticated user cannot accept invitations.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        client = APIClient()  # Unauthenticated client
        accept_url = reverse('tournament-invitation-accept-invitation', args=[invitation.id])
        response = client.put(accept_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refuse_invitation_when_user_not_authenticated(self):
        """
        Test that an unauthenticated user cannot refuse invitations.
        """
        invitation = TournamentInvitation.objects.create(tournament=self.tournament, from_player=self.player1, to_player=self.player2)
        client = APIClient()  # Unauthenticated client
        refuse_url = reverse('tournament-invitation-refuse-invitation', args=[invitation.id])
        response = client.put(refuse_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def test_player_statistics(self):
    """
    Test que les statistiques du joueur sont calculées correctement.
    """
    match1 = Game.objects.create(
        name="Match 1",
        player1=self.player1,
        player2=self.player2,
        status='completed',
        winner=self.player1,
        tournament=self.tournament
    )
    match2 = Game.objects.create(
        name="Match 2",
        player1=self.player1,
        player2=self.player3,
        status='completed',
        winner=self.player3,
        tournament=self.tournament
    )

    stats = self.player1.stats
    self.assertEqual(stats.matches_played, 2)
    self.assertEqual(stats.matches_won, 1)
    self.assertEqual(stats.matches_lost, 1)
    self.assertEqual(stats.win_rate, 50)
