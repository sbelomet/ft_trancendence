
from rest_framework import serializers
from .models import Player, Tournament, PlayerStatistics, TournamentInvitation
from urllib.parse import urlparse
from django.utils.timezone import now
from datetime import datetime, timedelta


class PlayerSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()  # Renvoie l'objet utilisateur sérialisé

    def get_avatarUrl(self, obj):
        avatar_url = obj.avatar.url
        parsed_url = urlparse(avatar_url)
        avatar_url = parsed_url.path # Remove the scheme and netloc (domain + port)
        if avatar_url.startswith('/media/https%3A/'):
            avatar_url = avatar_url.replace('/media/https%3A/', 'https://')
        return avatar_url
    avatar_url = serializers.SerializerMethodField('get_avatarUrl')

    def get_user(self, obj):
        from users.serializers import UserBaseSerializer  # Importation locale pour éviter les dépendances circulaires
        serializer = UserBaseSerializer(obj.user, context=self.context)
        return serializer.data

    def get_user_id(self, obj):
        return obj.user.id  # Retourne uniquement l'ID de l'utilisateur
    

    class Meta:
        model = Player
        fields = ['id', 'user_id', 'user', 'avatar_url', 'nickname', 'ranking']  # Inclure user_id et user
        extra_kwargs = {'nickname': {'required': False}}

class TournamentInvitationSerializer(serializers.ModelSerializer):
    tournament = serializers.PrimaryKeyRelatedField(queryset=Tournament.objects.all())
    class Meta:
        model = TournamentInvitation
        fields = ['id', 'tournament', 'from_player', 'to_player', 'created_at', 'is_confirmed']
        
    def validate_to_player(self, value):
        current_user = self.context['request'].user
        if not current_user.is_authenticated:
            raise serializers.ValidationError("You must be connected to invite players.")
        current_player = current_user.player_profile
        if value == current_player:
            raise serializers.ValidationError("You cannot invite yourself to the tournament.")
        return value

    def validate(self, data):
        tournament = data.get('tournament')
        to_player = data.get('to_player')
        if tournament.participants.filter(id=to_player.id).exists():
            raise serializers.ValidationError({"detail": "Player already a participant."})
        if tournament.max_players and tournament.participants.count() >= tournament.max_players:
            raise serializers.ValidationError({"detail": "The tournament is already full."})
        if tournament.status != 'upcoming':
            raise serializers.ValidationError({"detail": "The tournament has already began."})
        return data      
    
class TournamentSerializer(serializers.ModelSerializer):
    participants = PlayerSerializer(many=True, read_only=True)
    created_by = PlayerSerializer(read_only=True)
    invitations = TournamentInvitationSerializer(many=True, read_only=True, source='tournament_invitation_set')
    winner = PlayerSerializer(read_only=True)
    
    class Meta:
        model = Tournament
        fields = '__all__'
        read_only_fields = ['status', 'winner', 'participants', 'created_by', 'current_round', 'bye_player']
    
    def validate_max_players(self, value):
        if value < 3 or value > 20:
            raise serializers.ValidationError({"detail": "Player count should be between 3 and 20"})
        return value

    # Validate start_time
    def validate_start_time(self, value):
        current_time = now()  # Current time in UTC
        # Ensure start_time is in the future
        if value <= current_time:
            raise serializers.ValidationError("The start time must be in the future.")       
        elif value > current_time + timedelta(minutes=5):
            raise serializers.ValidationError("The start time mustn't be further than 5 minutes in the future.")
        return value
    



class PlayerStatisticsSerializer(serializers.ModelSerializer):
    matches_played = serializers.SerializerMethodField()
    matches_won = serializers.SerializerMethodField()
    matches_lost = serializers.SerializerMethodField()
    win_rate = serializers.SerializerMethodField()
    tournaments_played = serializers.SerializerMethodField()
    tournaments_won = serializers.SerializerMethodField()
    tournament_win_rate = serializers.SerializerMethodField()

    class Meta:
        model = PlayerStatistics
        fields = ['matches_played', 'matches_won', 'matches_lost', 'win_rate', 'tournaments_played', 'tournaments_won', 'tournament_win_rate']
        #read_only_fields = ['matches_played', 'matches_won', 'matches_lost', 'win_rate', 'tournaments_played', 'tournaments_won', 'tournament_win_rate']
    
    def get_matches_played(self, obj):
        return obj.matches_played
    
    def get_matches_won(self, obj):
        return obj.matches_won
    
    def get_matches_lost(self, obj):
        return obj.matches_lost
        
    def get_win_rate(self, obj):
        return obj.win_rate
    
    def get_tournaments_played(self, obj):
        return obj.tournaments_played
    
    def get_tournaments_won(self, obj):
        return obj.tournaments_won
    
    def get_tournament_win_rate(self, obj):
        return obj.tournament_win_rate
    

