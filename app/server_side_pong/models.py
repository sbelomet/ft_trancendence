from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

User = get_user_model()

# Games Model
class Game(models.Model):
    class Meta:
        ordering = ['-start_time']
    class Meta:
        ordering = ['-start_time']
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('interrupted', 'Interrupted'),
    ]
    TYPE_CHOICES = [
        ('local', 'Local'),
        ('remote', 'Remote'),
    ]
    name = models.CharField(max_length=200, unique=True)
    player1 = models.ForeignKey('matchmaking.Player', on_delete=models.CASCADE, null=True, blank=True, related_name='games_as_player1')
    player2 = models.ForeignKey('matchmaking.Player', on_delete=models.CASCADE, null=True, blank=True, related_name='games_as_player2')
    tournament = models.ForeignKey('matchmaking.Tournament', on_delete=models.CASCADE, null=True, blank=True, related_name='tournament_games')
    rounds_needed = models.IntegerField()
    round_number = models.IntegerField(default=0, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('matchmaking.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_games')
    game_type =  models.CharField(max_length=10, choices=TYPE_CHOICES)
    winner = models.ForeignKey('matchmaking.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='games_won')

#what / who uses this ?
    def create_guest_user(self):
        if self.created_by and self.created_by.user:
            guest_username = f"guest_{self.created_by.user.username}"
            guest_user = User.objects.create_user(
                username=guest_username,
                email=f"{guest_username}@random.com",
                password=get_random_string(10, allowed_chars='0123456789'),
                is_guest=True
            )
            return guest_user
        else:
            raise ValueError("No associated player.")

    def __str__(self):
        return f"Game {self.id} - {self.status}"

#score is to track the final result of one game, that is, who won. +1 is winner and 0 is looser
