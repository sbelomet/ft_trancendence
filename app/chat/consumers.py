import json
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, PrivateMessage, Notification
from users.models import Friendship
from django.db.models import Q

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.info()

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
	redis_client = redis.StrictRedis(host="redis", port=6380, db=0)
	async def connect(self):
		logger.info(f"Chat Consummer: {self.scope['user'].username} has connected")
		self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
		self.room_group_name = "chat_%s" % self.room_name
		self.user_group_name = f"user_{self.scope['user'].id}"

		#logger.info(f'id: {self.scope["user"].id}, user group name: {self.user_group_name}')

		# Join room group for gen chat and user group for private things (dms, notifs)
		await self.channel_layer.group_add(self.room_group_name, self.channel_name)
		await self.channel_layer.group_add(self.user_group_name, self.channel_name)

		await self.accept()

		# Send status update to all
		await self.channel_layer.group_send(
			self.room_group_name,
			{
				"type": "status_update",
				"senderID": self.scope['user'].id,
				"is_online": True
			})
	
	async def disconnect(self, close_code):
		logger.info(f"Chat Consummer: {self.scope['user'].username} has disconnected")

		# Send status update to all
		await self.channel_layer.group_send(
			self.room_group_name,
			{
				"type": "status_update",
				"senderID": self.scope['user'].id,
				"is_online": False
			})

		# Leave groups
		await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
		await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

	async def receive(self, text_data):
		# Receive message from WebSocket
		text_data_json = json.loads(text_data)
		logger.info(f'json thing: {text_data_json}')
		message_type = text_data_json["type"]

		if message_type == "chat_message":
			await self.handle_chat_message(text_data_json)
		elif message_type == "private_chat_message":
			await self.handle_private_chat_message(text_data_json)
		elif message_type == "notification":
			await self.handle_notification(text_data_json)
		elif message_type == "remove_notification":
			await self.remove_notification(text_data_json["notificationID"])
		elif message_type == "ping_response":
			await self.handle_ping_response(text_data_json)

	async def handle_ping_response(self, data):
		user_id = data["user_id"]
		tournament_id = data["tournament_id"]
		logger.info("got in handle ping response")
		self.redis_client.sadd(f"tournament_responses_{tournament_id}", user_id)

	async def handle_chat_message(self, data):
		message = data["message"]
		username = data["username"]
		avatarUrl = data["avatarUrl"]
		userID = data["userID"]
		room = data["room"]

		await self.save_message(userID, room, message)

		# Send message to room group
		await self.channel_layer.group_send(
			self.room_group_name,
			{
				"type": "chat_message",
				"message": message,
				"username": username,
				"avatarUrl": avatarUrl,
				"userID": userID
			})
		
	async def handle_private_chat_message(self, data):
		message = data["message"]
		sender_username = data["sender_username"]
		avatarUrl = data["avatarUrl"]
		senderID = data["senderID"]
		recipientID = data["recipientID"]

		# Check if the users are friends
		friends = await self.are_friends(senderID, recipientID)
		blocked = await self.is_blocked(senderID, recipientID)
		if not friends or blocked:
			logger.info(f'Private message blocked: {senderID} and {recipientID} are not friends')
			return

		await self.save_private_message(senderID, recipientID, message)

		# Send private message to recipient and sender
		await self.channel_layer.group_send(
			f"user_{recipientID}",
			{
				"type": "private_chat_message",
				"message": message,
				"sender_username": sender_username,
				"avatarUrl": avatarUrl,
				"senderID": senderID,
				"recipientID": recipientID
			})
		await self.channel_layer.group_send(
			f"user_{senderID}",
			{
				"type": "private_chat_message",
				"message": message,
				"sender_username": sender_username,
				"avatarUrl": avatarUrl,
				"senderID": senderID,
				"recipientID": recipientID
			})

	async def handle_notification(self, data):
		notification = data["notification"]
		message = data["message"]
		senderID = data["senderID"]
		senderName = data["senderName"]
		recipientID = data["recipientID"]
		requestID = data["requestID"]
		notificationID = -1

		if notification != "systemMessage":
			# Check if the recipient has blocked the sender
			blocked = await self.is_blocked(senderID, recipientID)
			if blocked:
				logger.info(f'Notification blocked: {senderID} is blocked by {recipientID}')
				return

			notificationID = await self.save_notification(notification, senderID, recipientID, requestID)

		# Send notification to recipient
		await self.channel_layer.group_send(
			f"user_{recipientID}",
			{
				"type": "notification",
				"notification": notification,
				"message": message,
				"senderID": senderID,
				"senderName": senderName,
				"recipientID": recipientID,
				"requestID": requestID,
				"notificationID": notificationID
			})

	async def chat_message(self, event):
		# Receive message from group
		message = event["message"]
		username = event["username"]
		avatarUrl = event["avatarUrl"]
		userID = event["userID"]

		# Check if the recipient has blocked the sender
		blocked = await self.is_blocked(self.scope['user'].id, userID)
		if blocked:
			logger.info(f'message blocked: {self.scope["user"].id} is blocked by {userID}')
			return

		# Send message to WebSocket
		await self.send(text_data=json.dumps({
			"type": "chat_message",
			"message": message,
			"username": username,
			"avatarUrl": avatarUrl,
			"userID": userID
			}))

	async def private_chat_message(self, event):
		# Receive private message from group
		message = event["message"]
		sender_username = event["sender_username"]
		avatarUrl = event["avatarUrl"]
		senderID = event["senderID"]
		recipientID = event["recipientID"]

		# Send private messsage to WebSocket
		await self.send(text_data=json.dumps({
			"type": "private_chat_message",
			"message": message,
			"sender_username": sender_username,
			"avatarUrl": avatarUrl,
			"senderID": senderID,
			"recipientID": recipientID
		}))

	async def notification(self, event):
		# Receive notification from group
		logger.info(f'event thing: {event}')
		notification = event["notification"]
		message = event["message"]
		senderID = event["senderID"]
		senderName = event["senderName"]
		recipientID = event["recipientID"]
		requestID = event["requestID"]
		notificationID = event["notificationID"]

		# Send notification to WebSocket
		await self.send(text_data=json.dumps({
			"type": "notification",
			"notification": notification,
			"message": message,
			"senderID": senderID,
			"senderName": senderName,
			"recipientID": recipientID,
			"requestID": requestID,
			"notificationID": notificationID
		}))

	async def tournament_update(self, event):
		logger.info("got da juice")
		# Receive tournament update from group
		logger.info(f'evnet: {event}')
		message = event["message"]
		game_id = event["game_id"]
		opponent_name = event["opponent_name"]
		tourney_id = event["tourney_id"]

		# Send tournament game id to WebSocket
		await self.send(text_data=json.dumps({
			"type": "tournament_update",
			"message": message,
			"game_id": game_id,
			"opponent_name": opponent_name,
			"tourney_id": tourney_id
		}))
	
	async def ping(self, event):
		logger.info("got a ping")
		ping_type = event["ping_type"]
		ping_id = event["ping_id"]

		if (ping_type == "tournament_ping"):
			logger.info("got tourney ping")
			await self.send(text_data=json.dumps({
					"type": "tournament_ping",
					"ping_id": ping_id

				}))
	
	async def status_update(self, event):
		logger.info("got a status update")
		senderID = event["senderID"]
		is_online = event["is_online"]
		
		# Update the user's online status
		await self.change_status(senderID, is_online)


	@sync_to_async
	def save_message(self, userID, room, message):
		try:
			user = User.objects.get(id=userID)
		except User.DoesNotExist:
			logger.error(f"User does not exist: senderID={userID}")
			return

		if message:
			if len(message) > 200:
				message = message[:200]  # Trim the message to 200 characters
			Message.objects.create(user=user, room=room, content=message)

	@sync_to_async
	def save_private_message(self, senderID, receiverID, message):
		try:
			sender = User.objects.get(id=senderID)
			receiver = User.objects.get(id=receiverID)
		except User.DoesNotExist:
			logger.error(f"User does not exist: senderID={senderID}, recipientID={receiverID}")
			return

		if message:
			if len(message) > 200:
				message = message[:200]  # Trim the message to 200 characters
			PrivateMessage.objects.create(sender=sender, receiver=receiver, content=message)

	@sync_to_async
	def save_notification(self, notification, senderID, recipientID, requestID):
		try:
			sender = User.objects.get(id=senderID)
			recipient = User.objects.get(id=recipientID)
		except User.DoesNotExist:
			logger.error(f"User does not exist: senderID={senderID}, recipientID={recipientID}")
			return -1

		new_notification = Notification.objects.create(
			sender=sender,
			recipient=recipient,
			notification=notification,
			requestID=requestID
		)
		return new_notification.id
	
	@sync_to_async
	def remove_notification(self, id):
		try:
			notification = Notification.objects.get(id=id)
			notification.delete()
		except Notification.DoesNotExist:
			logger.error(f"Notification does not exist: id={id}")

	@sync_to_async
	def is_blocked(self, senderID, recipientID):
		return Friendship.objects.filter(
			Q(from_user_id=recipientID, to_user_id=senderID, is_blocked=True) |
			Q(from_user_id=senderID, to_user_id=recipientID, is_blocked=True)
		).exists()

	@sync_to_async
	def are_friends(self, user1_id, user2_id):
		return Friendship.objects.filter(
			Q(from_user_id=user1_id, to_user_id=user2_id, has_rights=True) |
			Q(from_user_id=user2_id, to_user_id=user1_id, has_rights=True)
		).exists()

	@sync_to_async
	def change_status(self, senderID, is_online):
		try:
			user = User.objects.get(id=senderID)
			user.is_online = is_online
			user.save()
		except Notification.DoesNotExist:
			logger.error(f"User does not exist: senderID={senderID}")