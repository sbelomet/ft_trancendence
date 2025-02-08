from django.contrib import admin
from .models import Game

# Customizing the Game admin interface
@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'game_type', 'rounds_needed', 'start_time', 'end_time', 'status')  # Columns displayed in the list view
    list_filter = ('status', 'start_time')  # Filters for easy navigation
    search_fields = ('id',)  # Search bar to search by game ID
    ordering = ('-start_time',)  # Order by start time, most recent first

# Customizing the GamePlayer admin interface
# @admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'player', 'score', 'position')  # Columns displayed in the list view
    list_filter = ('game', 'position')  # Filters for easy navigation
    search_fields = ('player__username', 'game__id')  # Search bar to search by player username or game ID
    ordering = ('game', 'position')  # Order by game and player position
