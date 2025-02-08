from rest_framework import permissions
from .models import CustomUser, Friendship
from django.db.models import Q

#Q objects from django.db.models to perform an OR query.
class IsFriendOrSelf(permissions.BasePermission):
    message = "Only friends can see each others friends."
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if not isinstance(obj, CustomUser):
            return False
        
        if obj == request.user:
            return True
        
        is_friend = Friendship.objects.filter(
            Q(from_user=request.user, to_user=obj) |
            Q(from_user=obj, to_user=request.user),
            has_rights=True,
            is_blocked=False
        ).exists()

        return is_friend

class IsOwnerOrAdmin(permissions.BasePermission):
    message = "Only owner of a profile can do this action."
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
    message = "You are not allowed to do this action on this user."
    def has_object_permission(self, request, view, obj):
        return (request.user == obj.to_user)  or request.user.is_superuser