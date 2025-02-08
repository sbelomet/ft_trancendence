from django.contrib import admin
from .models import Player, PlayerStatistics, Tournament, TournamentInvitation

# Customizing the Game admin interface
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'nickname', 'ranking')  # Columns displayed in the list view
    list_filter = ('id', 'user')  # Filters for easy navigation
    search_fields = ('user', 'id')  # Search bar to search by game ID
    ordering = ('id',)  # Order by start time, most recent first

# Customizing the GamePlayer admin interface
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'start_time', 'status')  # Columns displayed in the list view
    list_filter = ('status', 'start_time')  # Filters for easy navigation
    search_fields = ('status', 'start_time')  # Search bar to search by player username or game ID
    ordering = ('start_time', 'status')  # Order by game and player position


# Customizing the GamePlayer admin interface
@admin.register(TournamentInvitation)
class TournamentInvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_player', 'to_player', 'created_at', 'is_confirmed')  # Columns displayed in the list view
    list_filter = ('from_player', 'to_player', 'is_confirmed')  # Filters for easy navigation
    search_fields = ('from_player', 'to_player', 'is_confirmed')  # Search bar to search by player username or game ID
    ordering = ('id', 'is_confirmed')  # Order by game and player position
