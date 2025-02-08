from rest_framework import permissions
from ..users.models import CustomUser, Friendship
from django.db.models import Q

#Q objects from django.db.models to perform an OR query.
class IsFriendOrSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if not isinstance(obj, CustomUser):
            return False
        
        if obj == request.user:
            return True
        
        return Friendship.objects.filter(
            (Q(from_user=request.user, to_user=obj) | Q(from_user=obj, to_user=request.user)),
            is_confirmed=True
        ).exists()


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if isinstance(obj, CustomUser): #Pour les objets du CustomUser
            return obj == request.user or request.user.is_superuser
        elif isinstance(obj, Friendship): #pour les objets de la friendship
            return (obj.from_user == request.user or obj.to_user == request.user) or request.user.is_superuser
        else:
            return False

    
class IsFriendshipRecipientOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user == obj.to_user)  or request.user.is_superuser