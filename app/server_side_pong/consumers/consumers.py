import json, asyncio, logging, sys, random, redis, pickle
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone  # To set the start time
from django.apps import apps #fix les probleme d'import
from channels.layers import get_channel_layer
from .utils import get_or_create_guest_player, adjust_ball_velocity
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PADDLE_SPEED = 3
BALL_SPEED = 1.05
BALL_RADIUS = 1.5
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 90
PADDLE_HEIGHT = 15
ROUND_NEEDED = 5
EPSILON = 1e-2
BALL_SPEED_STEP = 1.05
VXSPEED = 1
VYSPEED = 0.9

logger = logging.getLogger(__name__)
class GameManager:
    redis_client = redis.StrictRedis(host="redis", port=6380, db=0)
    _instances = {}  # In-memory cache for TwoPlayerPong instances

    @classmethod
    def create_game(cls, game_id):
        game_state = {
            "ball": { "x": 80, "y": 45, "vx": VXSPEED, "vy": VYSPEED },
            "players": {
                "player1": { "x": 10, "y": 36.5, "slide" : None},
                "player2": { "x": 150, "y": 36.5, "slide" : None},
            },
            "scores": { "player1": 0, "player2": 0 },
        }
        cls.redis_client.set(game_id, pickle.dumps(game_state))

    @classmethod
    def get_game_state(cls, game_id):
        game_data = cls.redis_client.get(game_id)
        if game_data is None:
            raise ValueError(f"Game {game_id} not found.")
        pickle.loads(game_data)
        # logger.info(f"Fetched game state for {game_id}: {game_state}")
        return pickle.loads(game_data)

    @classmethod
    def save_game_state(cls, game_id, game_state):
        # logger.info(f"Saving game state for {game_id}: {game_state}")
        cls.redis_client.set(game_id, pickle.dumps(game_state))

    @classmethod
    def get_game_instance(cls, game_id):
        if game_id not in cls._instances:
            game_state = cls.get_game_state(game_id)
            cls._instances[game_id] = TwoPlayerPong(game_id, game_state)
        return cls._instances[game_id]

    @classmethod
    def start_game(cls, game_id):
        """Start the game loop for the given game ID."""
        game_instance = cls.get_game_instance(game_id)
      #  game_state = GameManager.get_game_state(game_id)
      #  player1_id = game_state["players"]["player1"]["user_id"]
        """ asyncio.create_task(game_instance.check_tournament(player1_id))
        time.sleep(1) """
        asyncio.create_task(game_instance.start_game_loop())

    @classmethod
    def stop_game(cls, game_id):
        """Stop the game loop for the given game ID."""
        if game_id in cls._instances:
            game_instance = cls._instances[game_id]
            logger.info(f"Game_instance_loop id {game_id} has been stopped and killed due to disconnection")
            asyncio.create_task(game_instance.stop_game_loop())
            del cls._instances[game_id]

    @classmethod
    def add_player(cls, game_id, user_id):
        """Add a player to the game and assign a role."""
        logger.info(f"Attempting to add player {user_id} to game ID: {game_id}")
        game_state = cls.get_game_state(game_id)

        # Check if the player is already in the game
        existing_roles = [role for role in game_state["players"] if "user_id" in game_state["players"][role]]
        if user_id in [game_state["players"][role]["user_id"] for role in existing_roles]:
            logger.warning(f"Player {user_id} is already in the game ID: {game_id}")
            raise ValueError("Player is already in the game")

        # Assign roles dynamically
        if "user_id" not in game_state["players"]["player1"]:
            role = "player1"
        elif "user_id" not in game_state["players"]["player2"]:
            role = "player2"
        else:
            logger.error(f"Game with ID {game_id} is full")
            raise ValueError("Game is full")

        # Add the player to the game
        game_state["players"][role]["user_id"] = user_id
        cls.save_game_state(game_id, game_state)
        logger.info(f"Player {user_id} added to game ID: {game_id} with role {role}")
        return role

    @classmethod
    def game_exists(cls, game_id):
        """Check if a game exists in Redis."""
        return cls.redis_client.exists(game_id) > 0

    @classmethod
    def is_user_in_game(cls, game_id, user_id):
        """Check if a user is already in the game."""
        try:
            game_state = cls.get_game_state(game_id)
            return any(
                "user_id" in game_state["players"][role] and game_state["players"][role]["user_id"] == user_id
                for role in ["player1", "player2"]
            )
        except ValueError as e:
            logger.error(f"Error checking if user {user_id} is in game {game_id}: {e}")
            return False


logger = logging.getLogger(__name__)

class TwoPlayerPong:
    def __init__(self, game_id, game_state):
        self.game_id = game_id
        self.running = False
        self.game_state = game_state
        app_config = apps.get_app_config('server_side_pong')
        self.Game = app_config.get_model('Game')
        app_config_match = apps.get_app_config('matchmaking')
        self.Player = app_config_match.get_model('Player')
        self.Tournament = app_config_match.get_model('Tournament')
       # player1_id = game_state["players"]["player1"]["user_id"]
        #self.delay_first_round = False
       # asyncio.create_task(self.check_tournament(player1_id))

    """ async def check_tournament(self, player1_id):
        exists = await asyncio.to_thread(
            lambda: self.Tournament.objects.filter(participants__id=player1_id, status="ongoing").exists()
        )
        if exists:
            logger.info(f"Player {player1_id} is in an ongoing tournament. Delaying first round.")
            self.delay_first_round = True
        else:
            logger.info(f"Player {player1_id} is NOT in an ongoing tournament.") """

    async def start_game_loop(self):
        self.last_update_time = int(0)
        channel_layer = get_channel_layer()
        logger.info(f"Game loop in instance {self.game_id} is starting")

        
        """ if self.delay_first_round == True:
            logger.info(f"about to delay first round")
            await asyncio.sleep(9)
            logger.info(f"done delaying first round")
            self.delay_first_round = False """
        self.running = True
        


        time_elapsed = 0
        update_ball_delay = 3
        try:
            while self.running:

                self.game_state = GameManager.get_game_state(self.game_id)

                for role in ["player1","player2"]:
                    movement = self.game_state["players"][role].get("slide") #get is more error proof than accessing directily => returns None instead of crash if key doesnt exist
                    if movement == "w" or movement == "ArrowUp":
                        current_y = self.game_state["players"][role]["y"]
                        new_y = max(current_y - PADDLE_SPEED, 0)
                        self.game_state["players"][role]["y"] = new_y
                    elif movement == "s" or movement == "ArrowDown":
                        current_y = self.game_state["players"][role]["y"]
                        new_y = min(current_y + PADDLE_SPEED, SCREEN_HEIGHT - PADDLE_HEIGHT)
                        self.game_state["players"][role]["y"] = new_y

                GameManager.save_game_state(self.game_id, self.game_state)

                # Update game state
                if time_elapsed >= update_ball_delay:
                    await self.update_ball()
                
                # Broadcast the updated state
                await channel_layer.group_send(
                    f"game_{self.game_id}",
                    {
                        "type": "broadcast_game_state",
                        "state": { "type": "gameplay", "state": self.game_state },
                    },
                )

                await asyncio.sleep(1 / 60)  # 60 FPS

                time_elapsed += 1/60

        except asyncio.CancelledError:
            self.running = False

    async def stop_game_loop(self):
        self.running = False

    async def remote_update_state(self, role, data):
        if data["type"] == "gameplay":
            self.game_state = GameManager.get_game_state(self.game_id)
            action = data["action"]
            direction = data["movement"]
            if role in ["player1", "player2"]:
                if action == "keydown":
                    self.game_state["players"][role]["slide"] = direction
                    GameManager.save_game_state(self.game_id, self.game_state)
                elif action == "keyup":
                    self.game_state["players"][role]["slide"] = None
                    GameManager.save_game_state(self.game_id, self.game_state)

    async def local_update_state(self, exrole, data):
        # logger.info(f"message received as : {data}")
        if data["type"] == "gameplay":
            self.game_state = GameManager.get_game_state(self.game_id)
            direction = data["movement"]
            role = data["role"]
            action = data["action"]
            if action == "keydown":
                self.game_state["players"][role]["slide"] = direction
                GameManager.save_game_state(self.game_id, self.game_state)
            elif action == "keyup":
                self.game_state["players"][role]["slide"] = None
                GameManager.save_game_state(self.game_id, self.game_state)

    async def update_ball(self):
        self.game_state = GameManager.get_game_state(self.game_id)
        ball = self.game_state["ball"]

        # Predict the next position of the ball
        next_x = ball["x"] + ball["vx"]
        next_y = ball["y"] + ball["vy"]

        # Handle wall collisions (top/bottom)
        if next_y <= 0 or next_y >= SCREEN_HEIGHT:
            ball["vy"] = -ball["vy"]
            next_y = ball["y"] + ball["vy"]  # Update predicted position after collision

        player1 = self.game_state["players"]["player1"]
        player2 = self.game_state["players"]["player2"]

        #The collision logic works for "grazing" cases because it checks whether the path of the ball intersects with the paddle's boundary, 
        # rather than relying solely on the ball's exact position (next_x or next_y) during a single frame.
        # For player1's paddle
        if (
            ball["vx"] < 0 and # Ball is moving towards player1's paddle
            next_x - BALL_RADIUS <= player1["x"] <= ball["x"] + BALL_RADIUS and # Ball's path intersects the paddle's vertical plane
            player1["y"] <= next_y <= player1["y"] + PADDLE_HEIGHT # Ball's vertical position is within the paddle's range
        ):
            ball["vx"] = -ball["vx"]
            adjust_ball_velocity(ball, player1["y"], PADDLE_HEIGHT, BALL_SPEED_STEP)
            if next_x - BALL_RADIUS < player1["x"]:
                next_x = player1["x"] + BALL_RADIUS

        # For player2's paddle
        if (
            ball["vx"] > 0 and # Ball is moving towards player2's paddle
            ball["x"] - BALL_RADIUS <= player2["x"] <= next_x + BALL_RADIUS and # Ball's path intersects the paddle's vertical plane
            player2["y"] <= next_y <= player2["y"] + PADDLE_HEIGHT # Ball's vertical position is within the paddle's range
        ):
            ball["vx"] = -ball["vx"]
            adjust_ball_velocity(ball, player2["y"], PADDLE_HEIGHT, BALL_SPEED_STEP)
            if next_x + BALL_RADIUS > player2["x"]:
                next_x = player2["x"] - BALL_RADIUS

        # Update the ball's position after all collision checks
        ball["x"] = next_x
        ball["y"] = next_y

        # if ball["x"] < 10 or ball["x"] > 150:
        #     logger.info(f"Ball position is x:{ball['x']},y:{ball['y']}")

        GameManager.save_game_state(self.game_id, self.game_state)
        if ball["x"] <= 0 + EPSILON:
            self.game_state["scores"]["player2"] += 1
            GameManager.save_game_state(self.game_id, self.game_state)
            await self.end_of_round()
        elif ball["x"] >= SCREEN_WIDTH - EPSILON:
            self.game_state["scores"]["player1"] += 1
            GameManager.save_game_state(self.game_id, self.game_state)
            await self.end_of_round()

    async def end_of_round(self):
        await self.stop_game_loop()
        game = await sync_to_async(self.Game.objects.get)(id=self.game_id)
        player1score = self.game_state["scores"]["player1"]
        player2score = self.game_state["scores"]["player2"]
        if self.game_state["scores"]["player1"] == game.rounds_needed:
            logger.info(f"Right before end_of_game with game.rounds_needed being {game.rounds_needed} and player1 score being {player1score} ")
            await self.end_of_game("player1")
        elif self.game_state["scores"]["player2"] == game.rounds_needed:
            logger.info(f"Right before end_of_game with game.rounds_needed being {game.rounds_needed} and player1 score being {player2score} ")
            await self.end_of_game("player2")
        else:
            await self.reset_ball()
            await self.start_game_loop()

    async def end_of_game(self, winner):
        try:
            # Retrieve the game state from the GameManager
            game_state = GameManager.get_game_state(self.game_id)
            if not game_state:
                logger.error(f"Game state not found for game_id {self.game_id}")
                return

            # Determine the winner's user_id from the game state
            winner_user_id = game_state["players"].get(winner, {}).get("user_id")
            if not winner_user_id:
                logger.error(f"Winner user_id not found in game state for game_id {self.game_id} and winner {winner}")
                return
            logger.info(f"Winner user_id retrieved from game state: {winner_user_id}")

            # Fetch the Player model using the winner's user_id, with related fields preloaded
            try:
                winning_player = await sync_to_async(
                    self.Player.objects.select_related("user").get
                )(id=winner_user_id)
                logger.info(f"Winning player fetched with ID: {winning_player.id}")
            except self.Player.DoesNotExist:
                logger.error(f"Player with id {winner_user_id} does not exist")
                return

            # Fetch the game object
            try:
                game = await sync_to_async(self.Game.objects.get)(id=self.game_id)
            except self.Game.DoesNotExist:
                logger.error(f"Game with id {self.game_id} does not exist")
                return

            # Assign the winning player to the game.winner field
            game.winner = winning_player
            logger.info(f"Game {self.game_id} winner is being set to: {winning_player.id}")

            # Save the game object
            await sync_to_async(game.save)()
            logger.info(f"Game {self.game_id} saved with winner: {winning_player.id}")

            score = game_state["scores"]
            # Broadcast the game state as finished
            logger.info(f"Game {self.game_id} score is : {score}")
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f"game_{self.game_id}",
                {
                    "type": "broadcast_game_state",
                    "state": {"type": "ending", "state": "finished", "score": score, "winnerId": winning_player.id},
                },
            )

            # Update game status and end time
            game.end_time = timezone.now()
            game.status = "completed"
            await sync_to_async(game.save)()
            logger.info(f"Game {self.game_id} status updated to completed.")

        except Exception as e:
            logger.error(f"An unexpected error occurred in end_of_game: {e}")


    async def reset_ball(self):
        self.game_state["ball"] = {
            "x": SCREEN_WIDTH / 2,
            "y": SCREEN_HEIGHT / 2,
            "vx": BALL_SPEED * (-VXSPEED if random.random() < 0.5 else VXSPEED),
            "vy": BALL_SPEED * (-VYSPEED if random.random() < 0.5 else VYSPEED),
        }
        GameManager.save_game_state(self.game_id, self.game_state)

    async def get_state(self):
        return self.game_state


class RemotePongConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app_config = apps.get_app_config('server_side_pong')
        self.Game = app_config.get_model('Game')
        self.Player = apps.get_model('matchmaking', 'Player')
        self.CustomUser = apps.get_model('users', 'CustomUser')
        self.role = None

    async def connect(self):
        logger.info("WebSocket connection attempt.")
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        try:
            self.user_id = self.scope['user'].id
        except self.CustomUser.DoesNotExist:
            await self.close(code=4003)
            return

        self.group_name = f"game_{self.game_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        logger.info(f"User connected: {self.scope['user'].username}, user_id: {self.user_id}")

        if not GameManager.game_exists(self.game_id):
            logger.warning(f"Game with ID {self.game_id} does not exist.")
            await self.close(code=4003)
            return

        await self.accept()

        try:
            if GameManager.is_user_in_game(self.game_id, self.user_id):
                logger.info(f"User {self.user_id} is reconnecting to game {self.game_id}")
            else:
                self.role = GameManager.add_player(self.game_id, self.user_id)
            try:
                logger.info(f" self.role is {self.role}")
            except Exception as e:
                logger.error(f"Error logging self.role {e}")
            await self._assign_role_and_initialize_game()

            if self.role == "player2":
                game_state = GameManager.get_game_state(self.game_id)
                player1_user_id = game_state["players"]["player1"]["user_id"]
                player1 = await sync_to_async(self.Player.objects.get)(user__id=player1_user_id)
                player2 = await sync_to_async(self.Player.objects.get)(user__id=self.user_id)
                game = await self.Game.objects.aget(id=self.game_id)
                is_tournament = game.tournament_id is not None
                logger.info(f"Is it a tournament ? {is_tournament}")
                channel_layer = get_channel_layer()
                await channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "broadcast_init",
                        "message": {"type": "init", "player1" : player1.nickname, "player2": player2.nickname, "tournament": is_tournament},
                    }
                )
                GameManager.start_game(self.game_id)

        except ValueError as e:
            logger.error(f"Error during connection: {e}")
            await self.close(code=4001)

    async def _assign_role_and_initialize_game(self):
        game_model = await self.Game.objects.aget(id=self.game_id)
        try:
            player = await self.Player.objects.aget(user__id=self.user_id)
            # logger.warning(f"Player with user ID {self.user_id} exists and is .{player}")
        except self.Player.DoesNotExist:
            logger.warning(f"Player with user ID {self.user_id} does not exist.")
            return
        try:
            logger.info(f"Player with user ID {self.user_id} exists and its id is {player.id}")
        except Exception as e:
            logger.error(f"Error logging id of player of player 1: {e}")

        if player is None:
            logger.error("Player is not assigned!")
        else:
            logger.info(f"Player1 ID: {player.id}")

        try:
            logger.info(f"Player with user ID {self.user_id} exists and its role is  {self.role}")
        except Exception as e:
            logger.error(f"Error logging role: {e}")

        if self.role == "player1":
            if game_model.player1_id is None:
                game_model.player1 = player
            await self.send(text_data=json.dumps({"type": "role_assignment", "role": "player1"}))
        elif self.role == "player2":
            if game_model.player2_id is None:
                game_model.player2 = player
            game_model.status = "ongoing"
            game_model.start_time = timezone.now()
            await self.send(text_data=json.dumps({"type": "role_assignment", "role": "player2"}))

        await sync_to_async(game_model.save)()
        try:
            logger.info(f" game.player1.id is {game_model.player1.id}")
        except Exception as e:
            logger.error(f"Error logging game.player1.ID: {e}")
        try:
            logger.info(f" game.player2.id is {game_model.player2.id}")
        except Exception as e:
            logger.error(f"Error logging game.player2 ID: {e}")
        try:
            logger.info(f" game.status is {game_model.status}")
        except Exception as e:
            logger.error(f"Error logging game.status: {e}")

    async def disconnect(self, close_code):
        game = await sync_to_async(self.Game.objects.get)(id=self.game_id)
        if game.status == "ongoing":
            game_state = GameManager.get_game_state(self.game_id)
            if not game_state:
                logger.error(f"Game state not found for game_id {self.game_id}")
                return
            player1_id = game_state["players"]["player1"].get("user_id")
            player2_id = game_state["players"]["player2"].get("user_id")
            winner_id = player1_id if self.user_id != player1_id else player2_id
            try:
                winning_player = await sync_to_async(
                    self.Player.objects.select_related("user").get
                )(id=winner_id)
                logger.info(f"Winning player fetched with ID: {winning_player.id}")
            except self.Player.DoesNotExist:
                logger.error(f"Player with id {winner_id} does not exist")
                return
            try:
                loosing_player = await sync_to_async(
                    self.Player.objects.select_related("user").get
                )(id=self.user_id)
                logger.info(f"Loosing player fetched with ID: {self.user_id}")
            except self.Player.DoesNotExist:
                logger.error(f"Player with id {self.user_id} does not exist")
                return
            game.winner = winning_player
            logger.info(f"Game {self.game_id} winner is being set to:{winning_player.nickname} {winning_player.id} due to disconnection of opponent player with id {loosing_player.nickname} {self.user_id}")
            game.end_time = timezone.now()
            game.status = "completed"
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f"game_{self.game_id}",
                {
                    "type": "broadcast_game_state",
                    "state": {"type": "disconnection", "disconnected": loosing_player.nickname, "winner": winning_player.nickname},
                },
            )
            await sync_to_async(game.save)()
            GameManager.stop_game(self.game_id)
        elif game.status == "waiting":
            disconnector = await sync_to_async(self.Player.objects.select_related("user").get)(id=self.user_id)
            logger.info(f"Game {self.game_id} got killed because of premature disconnection of player {disconnector.nickname} with id{self.user_id}")
            game.end_time = timezone.now()
            game.status = "interrupted"
            await sync_to_async(game.save)()
            GameManager.stop_game(self.game_id)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except Exception as e:
            logger.error(f"Error processing received message: {e}")

        try:
            game_instance = GameManager.get_game_instance(self.game_id)
            await game_instance.remote_update_state(self.role, data)
        except ValueError as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def broadcast_game_state(self, event):
        await self.send(text_data=json.dumps(event["state"]))

    async def broadcast_init(self, event):
        await self.send(text_data=json.dumps(event["message"]))

###################LOCALLOCALLOCALLOCALLOCALLOCAL###############################################################

class LocalPongConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app_config = apps.get_app_config('server_side_pong')
        self.Game = app_config.get_model('Game')  # Use the correct model name
        self.Player = apps.get_model('matchmaking', 'Player')
        self.CustomUser = apps.get_model('users', 'CustomUser')
        self.role = None

    async def connect(self):
        logger.info("WebSocket connection attempt.")
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        try:
            self.user_id = self.scope['user'].id
        except self.CustomUser.DoesNotExist:
            await self.close(code=4003)  # Unauthorized
            return

        self.group_name = f"game_{self.game_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        if not GameManager.game_exists(self.game_id):
            logger.warning(f"Game with ID {self.game_id} does not exist")
            await self.close(code=4003)
            return

        await self.accept()

        try:
            if GameManager.is_user_in_game(self.game_id, self.user_id):
                logger.info(f"User {self.user_id} is reconnecting to game {self.game_id}")
            else:
                self.role = GameManager.add_player(self.game_id, self.user_id)
                await self._assign_role_and_initialize_game()
            player = await sync_to_async(self.Player.objects.get)(user__id=self.user_id)
            await self.send(text_data=json.dumps({"type": "init", "player1" : player.nickname, "player2": "Guest"}))
            GameManager.start_game(self.game_id)

        except ValueError as e:
            logger.error(f"Error during connection: {e}")
            await self.close(code=4001)

    async def _assign_role_and_initialize_game(self):
        game_model = await sync_to_async(self.Game.objects.get)(id=self.game_id)
        try:
            player = await sync_to_async(self.Player.objects.get)(user__id=self.user_id)
        except self.Player.DoesNotExist:
            logger.warning(f"Player with user ID {self.user_id} does not exist.")
            return

        if self.role == "player1":
            guest_player = await sync_to_async(get_or_create_guest_player)()
            GameManager.add_player(self.game_id, await sync_to_async(lambda: guest_player.user.id)())
            game_model.player1 = player
            game_model.player2 = guest_player
            game_model.status = "ongoing"
            game_model.start_time = timezone.now()

        await sync_to_async(game_model.save)()
        await self.send(text_data=json.dumps({
            "type": "role_assignment",
            "role": self.role,
        }))

    async def disconnect(self, close_code):
        game = await sync_to_async(self.Game.objects.get)(id=self.game_id)
        if game.status != "completed":
            game_state = GameManager.get_game_state(self.game_id)
            if not game_state:
                logger.error(f"Game state not found for game_id {self.game_id}")
                return
            player1_id = game_state["players"]["player1"].get("user_id")
            player2_id = game_state["players"]["player2"].get("user_id")
            winner_id = player1_id if self.user_id != player1_id else player2_id
            try:
                winning_player = await sync_to_async(
                    self.Player.objects.select_related("user").get
                )(id=winner_id)
                logger.info(f"Winning player fetched with ID: {winning_player.id}")
            except self.Player.DoesNotExist:
                logger.error(f"Player with id {winner_id} does not exist")
                return
            try:
                loosing_player = await sync_to_async(
                    self.Player.objects.select_related("user").get
                )(id=self.user_id)
                logger.info(f"Loosing player fetched with ID: {self.user_id}")
            except self.Player.DoesNotExist:
                logger.error(f"Player with id {self.user_id} does not exist")
                return
            game.winner = winning_player
            logger.info(f"Game {self.game_id} winner is being set to:{winning_player.nickname} {winning_player.id} due to disconnection of opponent player with id {loosing_player.nickname} {self.user_id}")
            game.end_time = timezone.now()
            game.status = "completed"
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f"game_{self.game_id}",
                {
                    "type": "broadcast_game_state",
                    "state": {"type": "disconnection", "disconnected": loosing_player.nickname, "winner": winning_player.nickname},
                },
            )
            await sync_to_async(game.save)()
            GameManager.stop_game(self.game_id)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        try:
            game_instance = GameManager.get_game_instance(self.game_id)
            await game_instance.local_update_state(self.role, data)
        except ValueError as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def broadcast_game_state(self, event):
        await self.send(text_data=json.dumps(event["state"]))