from django.db.models.signals import post_save
from django.dispatch import receiver
from server_side_pong.models import Game


@receiver(post_save, sender=Game)
def cleanup_guest_users(sender, instance, **kwargs):
	if instance.status == 'completed' and instance.is_local:
		guest = instance.player.filter(is_guest=instance.player.is_guest)
		guest.delete()