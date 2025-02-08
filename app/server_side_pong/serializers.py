from rest_framework import serializers
from .models import Game
from matchmaking.models import Player
from matchmaking.serializers import PlayerSerializer

class GameSerializer(serializers.ModelSerializer):
    winner = PlayerSerializer(read_only=True)

    class Meta:
        model = Game
        fields = ['id', 'name', 'player1', 'player2', 'tournament', 'rounds_needed',
                  'start_time', 'end_time', 'status', 'created_at', 'created_by', 'game_type', 'winner']
        read_only_fields = ['id', 'start_time', 'end_time',
                            'status', 'created_at', 'created_by', 'winner']

    def validate_rounds_needed(self, value):
        if value < 1:
            raise serializers.ValidationError({"detail":"Rounds needed must be at least 1."})
        elif value > 10:
            raise serializers.ValidationError({"detail":"Rounds needed must be at most 10."})
        return value

    def validate_game_type(self, value):
        if value not in ["local", "remote"]:
            raise serializers.ValidationError({"detail":"Game type must be either 'local' or 'remote'."})
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None

        if user:
            try:
                player, created = Player.objects.get_or_create(user=user, defaults={"nickname": user.username})
                validated_data['created_by'] = player
            except Player.DoesNotExist:
                raise serializers.ValidationError({"detail":"No associated Player exists for this User."})
            # Set initial status
            validated_data['status'] = 'waiting'

        # Create and return the Game instance
        game_instance = Game.objects.create(**validated_data)
        return game_instance


#NOTES regarding the meta class
#The Meta class in Django serializers defines metadata for the serializer, specifying the model it maps to and 
#which fields to include or exclude. It allows customization of serializer behavior, 
# as marking fields as read-only, setting default ordering, or defining additional options for model representation.

#NOTES regarding the player_ids entry in the meta class
#player_ids Is Custom-Defined:

#It’s a serializer-specific field used to: -Accept input from the API.
#-Validate the list of players.
#-Dynamically create the correct number of GamePlayer entries.
