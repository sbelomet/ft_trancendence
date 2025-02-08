from rest_framework import generics, permissions
from django.db.models import Q
from django.contrib.auth import get_user_model
import logging

from .models import Message, PrivateMessage, Notification
from users.models import Friendship
from .serializers import MessageSerializer, PrivateMessageSerializer, NotificationSerializer
from .pagination import CustomPagination

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# logger.info()

class MessageListView(generics.ListAPIView):
	serializer_class = MessageSerializer
	permission_classes = [permissions.IsAuthenticated]
	pagination_class = CustomPagination
	http_method_names = ['get']

	def get_queryset(self):
		user = self.request.user
		blocked_users = Friendship.objects.filter(
			Q(from_user=user, is_blocked=True) | Q(to_user=user, is_blocked=True)
		).values_list('from_user', 'to_user')

		blocked_user_ids = set()
		for from_user, to_user in blocked_users:
			if from_user == user.id:
				blocked_user_ids.add(to_user)
			else:
				blocked_user_ids.add(from_user)

		queryset = Message.objects.exclude(user__id__in=blocked_user_ids).order_by('-id')[:50]
		return list(queryset)[::-1]

class PrivateMessageListView(generics.ListAPIView):
	serializer_class = PrivateMessageSerializer
	permission_classes = [permissions.IsAuthenticated]
	pagination_class = CustomPagination
	http_method_names = ['get']

	def get_queryset(self):
		User = get_user_model()
		user = self.request.user
		other_user_id = self.request.query_params.get('other_user')
		if other_user_id:
			other_user = User.objects.get(id=other_user_id)
			queryset = PrivateMessage.objects.filter(
				Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user)
			).order_by('-id')[:50]
			return list(queryset)[::-1]
		return PrivateMessage.objects.none()

class NotificationListView(generics.ListAPIView):
	serializer_class = NotificationSerializer
	permission_classes = [permissions.IsAuthenticated]
	pagination_class = CustomPagination
	http_method_names = ['get']

	def get_queryset(self):
		user = self.request.user
		return Notification.objects.filter(recipient=user).order_by('-date_added')
