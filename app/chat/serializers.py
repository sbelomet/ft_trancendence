from rest_framework import serializers
from chat.models import Message, PrivateMessage, Notification
from urllib.parse import urlparse

class MessageSerializer(serializers.ModelSerializer):
	username = serializers.CharField(source='user.username', read_only=True)
	userID = serializers.IntegerField(source='user.id', read_only=True)

	def get_avatarUrl(self, obj):
		avatar_url = obj.user.avatar.url
		parsed_url = urlparse(avatar_url)
		avatar_url = parsed_url.path # Remove the scheme and netloc (domain + port)
		if avatar_url.startswith('/media/https%3A/'):
			avatar_url = avatar_url.replace('/media/https%3A/', 'https://')
		return avatar_url
	avatarUrl = serializers.SerializerMethodField('get_avatarUrl')

	class Meta:
		model = Message
		fields = ['id', 'user', 'username', 'avatarUrl', 'userID', 'room', 'content', 'date_added', 'time_diff']

class PrivateMessageSerializer(serializers.ModelSerializer):
	sender_username = serializers.CharField(source='sender.username', read_only=True)
	senderID = serializers.IntegerField(source='sender.id', read_only=True)
	receiver_username = serializers.CharField(source='receiver.username', read_only=True)

	def get_avatarUrl(self, obj):
		avatar_url = obj.sender.avatar.url
		parsed_url = urlparse(avatar_url)
		avatar_url = parsed_url.path # Remove the scheme and netloc (domain + port)
		if avatar_url.startswith('/media/https%3A/'):
			avatar_url = avatar_url.replace('/media/https%3A/', 'https://')
		return avatar_url
	avatarUrl = serializers.SerializerMethodField('get_avatarUrl')

	class Meta:
		model = PrivateMessage
		fields = ['id', 'sender', 'receiver', 'sender_username', 'senderID', 'avatarUrl', 'receiver_username', 'content', 'date_added', 'time_diff']

class NotificationSerializer(serializers.ModelSerializer):
	senderName = serializers.CharField(source='sender.username', read_only=True)
	senderID = serializers.IntegerField(source='sender.id', read_only=True)
	recipientName = serializers.CharField(source='recipient.username', read_only=True)
	#content_object = serializers.SerializerMethodField()

	class Meta:
		model = Notification
		fields = ['id', 'senderID', 'senderName', 'recipientName', 'notification', 'requestID', 'date_added']
