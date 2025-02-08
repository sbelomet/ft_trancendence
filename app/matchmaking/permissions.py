from rest_framework import permissions

class IsInvitedRecipientOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        #hasattr has attribut
        return request.user.is_superuser or (
            hasattr(request.user, 'player_profile') and request.user.player_profile == obj.to_player
        )
