from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Player, PlayerStatistics
from server_side_pong.models import Game

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.info()

#create automatically a player when a user is created
#create automatically a playerstatistic when a player is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_player(sender, instance, created, **kwargs):
    if created:
        #logger.info (f"user avatar {instance.avatar}")
        Player.objects.create(
            id=instance.id, #copier id pour etre la meme que le user associé
            avatar=instance.avatar,
            user=instance,
            nickname=instance.username
        )
        PlayerStatistics.objects.create(player_id=instance.id)
        


@receiver(post_save, sender=Game)
def check_tournament_progress(sender, instance, **kwargs):
    from .tasks import advance_tournament_round_task
    if instance.tournament and instance.status == 'completed':
        tournament = instance.tournament
        #checks if all games in current round are completed
        if not tournament.games.filter(round_number=tournament.current_round - 1, status__in=['scheduled', 'ongoing']).exists():
            # go to next round
            advance_tournament_round_task.delay(instance.tournament.id)


@receiver(post_save, sender=Game)
def update_player_statistics(sender, instance, **kwargs):
    # Mettre à jour les statistiques des joueurs après un match
    for player in [instance.player1, instance.player2]:
        if player is not None:
            stats, created = PlayerStatistics.objects.get_or_create(player=player)
            stats.matches_played = player.match_history.count()
            stats.matches_won = player.match_history.filter(winner=player).count()
            stats.save()