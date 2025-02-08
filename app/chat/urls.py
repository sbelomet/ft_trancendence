from django.urls import path
from .views import MessageListView, PrivateMessageListView, NotificationListView


urlpatterns = [
	path('chat/messages/', MessageListView.as_view(), name='message-list'),
	path('chat/private-messages/', PrivateMessageListView.as_view(), name='private-message-list'),
	path('chat/notifications/', NotificationListView.as_view(), name='notification-list'),
]