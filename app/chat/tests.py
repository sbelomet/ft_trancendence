from django.test import TestCase
from django.contrib.auth import get_user_model

#from .consumers import ChatConsumer
from .models import Message, PrivateMessage

User = get_user_model()

class MessageModelTest(TestCase):
	def setUp(self):
		self.user1 = User.objects.create_user(username='user1', password='password1', email='user1@a.com')
		self.user2 = User.objects.create_user(username='user2', password='password2', email='user2@a.com')
		self.room_name = 'test_room'

	def test_message_creation(self):
		"""Test the creation of a message and the default user"""
		message = Message.objects.create(user=self.user1, room=self.room_name, content='Hello, world!')
		self.assertEqual(message.user.username, 'user1')
		self.assertEqual(message.room, self.room_name)
		self.assertEqual(message.content, 'Hello, world!')
		self.assertIsNotNone(message.date_added)
		self.assertIsNone(message.time_diff)

	def test_time_diff_calculation(self):
		"""Test the calculation of time_diff between messages"""
		message1 = Message.objects.create(user=self.user1, room=self.room_name, content='First message')
		message2 = Message.objects.create(user=self.user1, room=self.room_name, content='Second message')

		self.assertIsNone(message1.time_diff)
		self.assertIsNotNone(message2.time_diff)
		#self.assertGreater(message2.time_diff, 0)

	def test_message_ordering(self):
		"""Test the ordering of messages by date_added"""
		message1 = Message.objects.create(user=self.user1, room=self.room_name, content='First message')
		message2 = Message.objects.create(user=self.user1, room=self.room_name, content='Second message')
		message3 = Message.objects.create(user=self.user2, room=self.room_name, content='Third message')

		messages = Message.objects.filter(room=self.room_name)
		self.assertEqual(messages[0], message1)
		self.assertEqual(messages[1], message2)
		self.assertEqual(messages[2], message3)

class PrivateMessageModelTest(TestCase):
	def setUp(self):
		self.user1 = User.objects.create_user(username='user1', password='password1', email='user1@a.com')
		self.user2 = User.objects.create_user(username='user2', password='password2', email='user2@a.com')

	def test_private_message_creation(self):
		"""Test the creation of a private message"""
		private_message = PrivateMessage.objects.create(sender=self.user1, receiver=self.user2, content='Hello, user2!')
		self.assertEqual(private_message.sender.username, 'user1')
		self.assertEqual(private_message.receiver.username, 'user2')
		self.assertEqual(private_message.content, 'Hello, user2!')
		self.assertIsNotNone(private_message.date_added)
		self.assertIsNone(private_message.time_diff)

	def test_time_diff_calculation(self):
		"""Test the calculation of time_diff between private messages"""
		private_message1 = PrivateMessage.objects.create(sender=self.user1, receiver=self.user2, content='First message')
		private_message2 = PrivateMessage.objects.create(sender=self.user1, receiver=self.user2, content='Second message')

		self.assertIsNone(private_message1.time_diff)
		self.assertIsNotNone(private_message2.time_diff)
		#self.assertGreater(private_message2.time_diff, 0)

	def test_private_message_ordering(self):
		"""Test the ordering of private messages by date_added"""
		private_message1 = PrivateMessage.objects.create(sender=self.user1, receiver=self.user2, content='First message')
		private_message2 = PrivateMessage.objects.create(sender=self.user1, receiver=self.user2, content='Second message')
		private_message3 = PrivateMessage.objects.create(sender=self.user2, receiver=self.user1, content='Third message')

		private_messages = PrivateMessage.objects.filter(sender=self.user1, receiver=self.user2)
		self.assertEqual(private_messages[0], private_message1)
		self.assertEqual(private_messages[1], private_message2)

		private_messages = PrivateMessage.objects.filter(sender=self.user2, receiver=self.user1)
		self.assertEqual(private_messages[0], private_message3)
