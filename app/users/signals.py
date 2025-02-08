from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from .models import Friendship

#The underscore (_) is used as a placeholder for the second value returned by 
# get_or_create, which is created. It's a Python convention to indicate that the value 
# is intentionally ignored because it’s not needed.
@receiver(post_save, sender='server_side_pong.Game')
def update_player_statistics(sender, instance, created, **kwargs):
    if instance.status == 'completed':
        PlayerStatistics = apps.get_model('matchmaking', 'PlayerStatistics')

# Logique détaillée:
#demande d'ami rights = False et  blocked = False
#création d'une amitiée en validant une request et création d'une double entrée (a->b et b->a):
# => cela fait 2 relation avec rights = True et  blocked = False
# => un user bloqué ne pourra pas interragir avec la personne qui l'a bloqué qu'importe si ce n'est pas lui qui a bloqué
# création d'un bloquge entre user A qui bloque user B (amis ou pas)
#       A => rights = True et  blocked = True
#       B => rights = False et  blocked = True
# le rights indique qui a bloqué et seulement ce user peut débloquer la relation
# après la débloquage la relations n'existe plus (plus amis)
@receiver(post_save, sender=Friendship)
def update_reverse_friendship(sender, instance, created, **kwargs):
    #très attention à la récursion!!!
    #si on a déjà mis le flag sur la row "instance" => stop.
    if getattr(instance, '_disable_signals', False):
        return

    #On flag l'instance pour éviter de retomber dans le signal
    setattr(instance, '_disable_signals', True)

    from_user = instance.from_user
    to_user   = instance.to_user

    # 3) check/find si row inverse
    reverse = Friendship.objects.filter(
        from_user=to_user, 
        to_user=from_user
    ).first()
    print(f"user: {from_user}, inst id: {instance.id}, has rights: {instance.has_rights}")
    #Logique de synchronisation
    if instance.has_rights:
        #on VEUT qu'il y ait un row inverse => on le crée si il n'existe pas
        reverse_rights = False
        if not reverse:
            if (instance.is_blocked == False): # in case of accepting a friend request, else blocking a not-friend user
                reverse_rights = True
            print(f"user: {from_user}, inst id: {instance.id}, revers rights: {reverse_rights}")
            reverse = Friendship(
                from_user=to_user,
                to_user=from_user,
                has_rights=reverse_rights,
                is_blocked=instance.is_blocked
            )
            #flag pour que le signal du "reverse.save()" ne reboucle pas.
            setattr(reverse, '_disable_signals', True)
            reverse.save()
        else:
            print("Blocking a friend")
            # row existe example si blockage d'un ami
            if (not instance.is_blocked):
                reverse_rights = True
            setattr(reverse, '_disable_signals', True)
            reverse.has_rights = reverse_rights
            reverse.is_blocked = instance.is_blocked
            reverse.save()
    else:
        # case of creating a friend request (is_blocked=False, has_rights=False)
        # no rights only in case of creating a friend request
        # to change an existing reciproque relationship the user has to have rights to do it (friend or user who blocked)
        pass