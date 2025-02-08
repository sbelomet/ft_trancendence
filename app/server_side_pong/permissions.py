from rest_framework import permissions
from .models import Game
from django.db.models import Q

#Q objects from django.db.models to perform an OR query.
class IsGamePlayer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return Game.objects.filter(
            (Q(from_user=request.user, to_user=obj) | Q(from_user=obj, to_user=request.user)),
            is_confirmed=True
        ).exists()

class IsCreatorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if isinstance(obj, Game):
            return (obj.from_user == request.user or obj.to_user == request.user) or request.user.is_superuser
        else:
            return False