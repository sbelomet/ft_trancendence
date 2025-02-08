from celery import shared_task
from .models import Player, Tournament
from django.utils.timezone import now
from django.db.models import Count
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json, time
import asyncio
import redis

logger = logging.getLogger(__name__)
@shared_task
def launch_tournaments():
	try:
		logger.info("Starting launch_tournaments task.")
		current_time = now()
		channel_layer = get_channel_layer()

		# cas 1 a le min de participants
		tournaments_to_start = Tournament.objects.annotate(num_participants=Count('participants')).filter(
			start_time__lte=current_time,
			status='upcoming',
			num_participants__gte=3
		)
		for tournament in tournaments_to_start:
			logger.info(f"Starting tournament: {tournament.name}")

			# Send ping to all participants
			participants = list(tournament.participants.all())
			for participant in participants:
				async_to_sync(channel_layer.group_send)(
					f"user_{participant.id}",
					{
						"type": "ping",
						"ping_type": "tournament_ping",
						"ping_id": tournament.id
					}
				)

			# Wait for responses from all participants
			all_responded = asyncio.run(wait_for_responses(participants, tournament.id))
			if not all_responded:
				logger.warning(f"Not all participants responded for tournament: {tournament.name}")
				for participant in participants:
					async_to_sync(channel_layer.group_send)(
								f"user_{participant.id}",
								{
									"type": "notification",
									"notification": "systemMessage",
									"message": "Somebody disconnected before the start of the tournament, sorry :/",
									"senderID": participant.id,
									"senderName": participant.user.username,
									"recipientID": participant.id,
									"requestID": tournament.id,
									"notificationID": -1
								}
							)
				tournament.delete()
				continue

			tournament.status = 'ongoing'
			game_dict = tournament.generate_initial_matches()
			game_dict_json = json.dumps(game_dict, default=str)
			tournament.save()
			logger.info(f"The tournament {tournament.name} is ready to start.")
			logger.info(f"in tasks.py: game dict: {game_dict}, game dict json: {game_dict_json}")
			for participant in participants:
				for key, value in game_dict.items():
					if participant.id in value:
						opponent_id = value[0] if value[1] == participant.id else value[1]
						opponent = Player.objects.get(id=opponent_id)
						async_to_sync(channel_layer.group_send)(
							f"user_{participant.id}",
							{
								"type": "tournament_update",
								"message": "start_countdown",
								"game_id": key,
								"opponent_name": opponent.user.username,
								"tourney_id": tournament.id
							}
						)
			time.sleep(5)
			# Send ping to all participants
			for participant in participants:
				async_to_sync(channel_layer.group_send)(
					f"user_{participant.id}",
					{
						"type": "ping",
						"ping_type": "tournament_ping",
						"ping_id": tournament.id
					}
				)

			# Wait for responses from all participants
			all_responded = asyncio.run(wait_for_responses(participants, tournament.id))
			if not all_responded:
				logger.warning(f"Not all participants responded for tournament: {tournament.name}")
				for participant in participants:
					async_to_sync(channel_layer.group_send)(
								f"user_{participant.id}",
								{
									"type": "notification",
									"notification": "systemMessage",
									"message": "Somebody disconnected during the tournament, sorry :/",
									"senderID": participant.id,
									"senderName": participant.user.username,
									"recipientID": participant.id,
									"requestID": tournament.id,
									"notificationID": -1
								}
							)
				tournament.delete()
				return
			# Send the game_ids to the players
			for participant in participants:
				for key, value in game_dict.items():
					if participant.id in value:
						opponent_id = value[0] if value[1] == participant.id else value[1]
						opponent = Player.objects.get(id=opponent_id)
						async_to_sync(channel_layer.group_send)(
							f"user_{participant.id}",
							{
								"type": "tournament_update",
								"message": "",
								"game_id": key,
								"opponent_name": opponent.user.username,
								"tourney_id": tournament.id
							}
						)
			if tournament.bye_player:
				#logger.info(f"Participant {tournament.bye_player.user.username} is waiting")
				async_to_sync(channel_layer.group_send)(
					f"user_{tournament.bye_player.id}",
					{
						"type": "notification",
						"notification": "systemMessage",
						"message": "The tournament started with an odd number of players and you gotta wait, sorry :/",
						"senderID": tournament.bye_player.id,
						"senderName": tournament.bye_player.user.username,
						"recipientID": tournament.bye_player.id,
						"requestID": tournament.id,
						"notificationID": -1
					}
				)


		# cas 2 doit être détruit
		tournaments_to_cancel = Tournament.objects.annotate(num_participants=Count('participants')).filter(
			start_time__lte=current_time,
			status='upcoming',
			num_participants__lt=3
		)
		for tournament in tournaments_to_cancel:
			#logger.info(f"The tournament {tournament.name} was cancelled due to insufficient number of participants.")
			participants = list(tournament.participants.all())
			for participant in participants:
				async_to_sync(channel_layer.group_send)(
							f"user_{participant.id}",
							{
								"type": "notification",
								"notification": "systemMessage",
								"message": "The tournament didn't have enough players to start, sorry :/",
								"senderID": participant.id,
								"senderName": participant.user.username,
								"recipientID": participant.id,
								"requestID": tournament.id,
								"notificationID": -1
							}
						)
			tournament.delete()

	except Exception as e:
		logger.exception("Error in launch_tournaments task")

@shared_task
def advance_tournament_round_task(tournament_id):
	try:
		channel_layer = get_channel_layer()
		tournament = Tournament.objects.get(id=tournament_id)
		game_dict = tournament.advance_tournament_round()
		#logger.info("got out of tournament.advance_tournament_round()")
		if game_dict: # if game_dict has no games in it, then the tournament is over
			#logger.info(f"in tasks.py: NEXXXTTTTT game dict: {game_dict}")
			participants = list(tournament.participants.all())
			for participant in participants:
				for key, value in game_dict.items():
					if participant.id in value:
						opponent_id = value[0] if value[1] == participant.id else value[1]
						opponent = Player.objects.get(id=opponent_id)
						async_to_sync(channel_layer.group_send)(
							f"user_{participant.id}",
							{
								"type": "tournament_update",
								"message": "start_countdown",
								"game_id": key,
								"opponent_name": opponent.user.username,
								"tourney_id": tournament.id
							}
						)
			time.sleep(5)
			# Send ping to all participants
			for participant in participants:
				async_to_sync(channel_layer.group_send)(
					f"user_{participant.id}",
					{
						"type": "ping",
						"ping_type": "tournament_ping",
						"ping_id": tournament.id
					}
				)

			# Wait for responses from all participants
			all_responded = asyncio.run(wait_for_responses(participants, tournament.id))
			if not all_responded:
				logger.warning(f"Not all participants responded for tournament: {tournament.name}")
				for participant in participants:
					async_to_sync(channel_layer.group_send)(
								f"user_{participant.id}",
								{
									"type": "notification",
									"notification": "systemMessage",
									"message": "Somebody disconnected during the tournament, sorry :/",
									"senderID": participant.id,
									"senderName": participant.user.username,
									"recipientID": participant.id,
									"requestID": tournament.id,
									"notificationID": -1
								}
							)
				tournament.delete()
				return
			for participant in participants:
				for key, value in game_dict.items():
					if participant.id in value:
						opponent_id = value[0] if value[1] == participant.id else value[1]
						opponent = Player.objects.get(id=opponent_id)
						async_to_sync(channel_layer.group_send)(
								f"user_{participant.id}",
								{
									"type": "tournament_update",
									"message": "",
									"game_id": key,
									"opponent_name": opponent.user.username,
									"tourney_id": tournament.id
								}
							)
			if tournament.bye_player:
				#logger.info(f"Participant {tournament.bye_player.user.username} is waiting")
				async_to_sync(channel_layer.group_send)(
					f"user_{tournament.bye_player.id}",
					{
						"type": "notification",
						"notification": "systemMessage",
						"message": "The tournament started with an odd number of players and you gotta wait, sorry :/",
						"senderID": tournament.bye_player.id,
						"senderName": tournament.bye_player.user.username,
						"recipientID": tournament.bye_player.id,
						"requestID": tournament.id,
						"notificationID": -1
					}
				)
	except Exception as e:
		logger.exception(f"Error advancing tournament round: {e}")

async def wait_for_responses(participants, tournament_id):
	redis_client = redis.StrictRedis(host='redis', port=6380, db=0)
	responses = set()

	async def wait_for_all_responses():
		while len(responses) < len(participants):
			redis_responses = redis_client.smembers(f"tournament_responses_{tournament_id}")
			responses.update(redis_responses)
			await asyncio.sleep(0.1)

	try:
		await asyncio.wait_for(wait_for_all_responses(), timeout=3.0)
	except asyncio.TimeoutError:
		logger.warning("Timeout waiting for responses")

	redis_client.delete(f"tournament_responses_{tournament_id}")

	return len(responses) == len(participants)