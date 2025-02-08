from django.contrib import admin 
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Friendship

#  django.contrib pour l'interface d'administration Django.
# création d'un type ce client admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['id', 'username', 'email', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['id']

#enregistrement de modèles
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Friendship)

#jbidaux : tu peux utiliser "@admin.register(CustomUser)" au dessus de ta class CustomUserAdmin
#et enlever la ligne equivalente en dessous de enregistrement de modele pour plus de swag