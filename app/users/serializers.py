from rest_framework import serializers
from .models import CustomUser, Friendship
from matchmaking.serializers import PlayerStatisticsSerializer
from django.conf import settings
from django.contrib.auth import authenticate
from server_side_pong.serializers import GameSerializer
import pyotp
from django.apps import apps
from django.db.models import Q

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.info()

#la classe Meta dans un serializer sert de validator, pour s'assurer
#que le model est le bon est les données correspondent bien
#et il converti les données en format JSON ou XML 
class UserBaseSerializer(serializers.ModelSerializer):
    player_profile = serializers.PrimaryKeyRelatedField(read_only=True)
    avatar = serializers.SerializerMethodField()
    nickname = serializers.CharField(source='player_profile.nickname', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id','username', 'nickname', 'email', 'avatar', 'remote_user', 'is_online', 'enable_2fa', 'player_profile']
        read_only_fields = ['is_online', 'id']

    def get_avatar(self, obj):
        #forcer à toujour retourner /media/avatar/etc
        if not obj.avatar:
            return None
        # Check if the avatar is a remote URL
        if obj.avatar.name.startswith("http://") or obj.avatar.name.startswith("https://"):
            return obj.avatar.name
        return f"{settings.MEDIA_URL}{obj.avatar.name}"

class UserSerializer(UserBaseSerializer):
    password = serializers.CharField(write_only=True, min_length=8, 
                required=False, style={'input_type': 'password'})
    avatar = serializers.ImageField(required=False)

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ['password']
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        enable_2fa = validated_data.get('enable_2fa', None)
        avatar = validated_data.pop('avatar', None)

        # If switching to TOTP, generate a new secret
        if enable_2fa == 'totp':
            instance.otp_secret = pyotp.random_base32()
            print(f"Generated new otp_secret: {instance.otp_secret}")
            
        if avatar:
            try:
                instance.avatar = avatar
            except Exception as e:
                raise serializers.ValidationError({"avatar": "Failed to upload avatar."})


        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

class UserPublicSerializer(UserBaseSerializer):
    match_history = GameSerializer(many=True, read_only=True)
    class Meta(UserBaseSerializer.Meta):
        fields = ['id', 'username', 'nickname', 'player_profile', 'avatar', 'is_online', 'match_history']
        read_only_fields = fields

        
class UserDetailSerializer(UserBaseSerializer):
    friends = serializers.SerializerMethodField()
    blocked = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    match_history = serializers.SerializerMethodField()

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ['friends', 'blocked', 'match_history', 'stats']

    def get_friends(self, obj):
        friendships = Friendship.objects.filter(
            Q(from_user=obj) | Q(to_user=obj),
            has_rights=True, 
            is_blocked=False
        ).select_related('from_user', 'to_user')
        friends = set()
        for friendship in friendships:
            if friendship.from_user == obj:
                friends.add(friendship.to_user)
            else:
                friends.add(friendship.from_user)
        serializer = UserPublicSerializer(friends, many=True, context=self.context)
        return serializer.data

    def get_blocked(self, obj):
        friendships = Friendship.objects.filter(
            Q(from_user=obj) | Q(to_user=obj),
            is_blocked=True
        ).select_related('from_user', 'to_user')

        blocked = set()
        for friendship in friendships:
            if friendship.from_user == obj:
                blocked.add(friendship.to_user)
            else:
                blocked.add(friendship.from_user)

        serializer = UserPublicSerializer(blocked, many=True, context=self.context)
        return serializer.data

    def get_match_history(self, obj):
        self.Player = apps.get_model('matchmaking', 'Player')
        try:
            player = obj.player_profile
            games = player.match_history  # Using the property from Player model
            serializer = GameSerializer(games, many=True, context=self.context)
            return serializer.data
        except self.Player.DoesNotExist:
            return []

    def get_stats(self, obj):
        self.PlayerStatistics = apps.get_model('matchmaking', 'PlayerStatistics')
        try:
            player_stats = obj.player_profile.stats
            return PlayerStatisticsSerializer(player_stats).data
        except self.PlayerStatistics.DoesNotExist:
            return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, 
                                     style={'input_type': 'password'}, min_length=8)
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'avatar', 'enable_2fa']

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError({"detail":"This username is not available."})
        return value
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError({"detail":"This email is already in use."})
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        avatar = validated_data.pop('avatar', None)
        user = CustomUser(**validated_data)

        if avatar:
            try:
                user.avatar = avatar
            except Exception as e:
                raise serializers.ValidationError({"avatar": "Failed to upload avatar."})
        user.set_password(password)  # Hash le mot de passe
        if user.enable_2fa:
            user.otp_secret = pyotp.random_base32()
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, 
                                     style={'input_type': 'password'})
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError({"detail":"Incorrect credentials."})
            if not user.is_active:
                raise serializers.ValidationError({"detail": "Deactivated user."})
            return user
        else:
            raise serializers.ValidationError({"detail":"Please enter username and password."})

class FriendshipSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    from_user = serializers.PrimaryKeyRelatedField(read_only=True)
    to_user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'is_blocked', 'created_at', 'has_rights']
        read_only_fields = ['from_user', 'created_at']
    
    def validate_to_user(self, value):
        user = self.context['request'].user
        #is_blocked_request = self.context['request'].data.get('is_blocked', False)
        
        if not user.is_authenticated:
            raise serializers.ValidationError({"detail":"You have to be logged in to send a friend request."})
        if value == user:
            raise serializers.ValidationError({"detail":"You cannot add yourself as a friend."})
        
        blocked_cold = Friendship.objects.filter(
            from_user=value,
            to_user=user,
            is_blocked=True,
            has_rights=True
        ).exists()
        if blocked_cold:
            raise serializers.ValidationError(
                {"detail":"This user has blocked you (cold block). You cannot send a friend request."}
            )
        return value
    
    
    def validate(self, data):
        user = self.context['request'].user
        to_user = data.get('to_user')
        is_blocked_request = self.context['request'].data.get('is_blocked', 'False') == 'True'
        # Vérifie que la relation n'est pas déjà confirmée ou bloquée
        #méthode .first() permet de ne prendre qu'une seule relation si plusieurs existent
        existing_friendship = Friendship.objects.filter(
            Q(from_user=user, to_user=to_user) |
            Q(from_user=to_user, to_user=user)
        ).first()
        if existing_friendship:
            if existing_friendship.has_rights and not is_blocked_request:
                raise serializers.ValidationError({"detail":"You are already friends with this user."})
            if existing_friendship.is_blocked and is_blocked_request:
                raise serializers.ValidationError({"detail":"You already blocked this user."})
        return data

        
