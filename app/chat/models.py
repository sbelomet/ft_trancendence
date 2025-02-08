from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()

class Message(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
	room = models.CharField(max_length=255)
	content = models.TextField()
	date_added = models.DateTimeField(auto_now_add=True)
	time_diff = models.IntegerField(null=True, blank=True)

	class Meta:
		ordering = ('date_added',)

	def save(self, *args, **kwargs):
		if not self.pk:  # Only calculate time_diff for new messages
			previous_message = Message.objects.filter(room=self.room).order_by('-date_added').first()
			if previous_message:
				time_difference = timezone.now() - previous_message.date_added
				self.time_diff = int(time_difference.total_seconds())
		super().save(*args, **kwargs)

	def __str__(self):
		return f"Message from {self.user.username} in {self.room}"

class PrivateMessage(models.Model):
	sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
	receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
	content = models.TextField()
	date_added = models.DateTimeField(auto_now_add=True)
	time_diff = models.IntegerField(null=True, blank=True)

	class Meta:
		ordering = ('date_added',)

	def save(self, *args, **kwargs):
		if not self.pk:  # Only calculate time_diff for new messages
			previous_message = PrivateMessage.objects.filter(sender=self.sender, receiver=self.receiver).order_by('-date_added').first()
			if previous_message:
				time_difference = timezone.now() - previous_message.date_added
				self.time_diff = int(time_difference.total_seconds())
		super().save(*args, **kwargs)

	def __str__(self):
		return f"Message from {self.sender.username} to {self.receiver.username}"
	
class Notification(models.Model):
	NOTIFICATION_TYPES = (
		('friendReq', 'Friend Request'),
		('gameInvite', 'Game Invite'),
	)

	sender = models.ForeignKey(User, related_name='notifications_sent', on_delete=models.CASCADE)
	recipient = models.ForeignKey(User, related_name='notifications_received', on_delete=models.CASCADE)
	notification = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
	requestID = models.PositiveIntegerField()
	date_added = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Notification from {self.sender.username} to {self.recipient.username} ({self.notification})"