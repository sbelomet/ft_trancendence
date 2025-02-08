import random
from django.apps import apps #fix les probleme d'import
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

def initialize_ball_velocity(ball_speed):
    # Randomly set the direction of vx and vy
    vx = random.choice([-1, 1]) * ball_speed
    vy = random.choice([-1, 1]) * ball_speed
    return vx, vy

def adjust_ball_velocity_obsolete(ball, paddle, paddle_length, horizontal=False, increase_factor=1.5):
    # Determine where the ball hit on the paddle
    relative_position = (ball["x"] - paddle["x"]) if horizontal else (ball["y"] - paddle["y"])
    section_length = paddle_length / 4

    # Adjust velocity based on section
    if relative_position < section_length:  # 1st section (leftmost or topmost)
        if horizontal:
            ball["vx"] *= increase_factor
        else:
            ball["vy"] *= increase_factor
    elif relative_position < 2 * section_length:  # 2nd section
        pass  # No change
    elif relative_position < 3 * section_length:  # 3rd section
        pass  # No change
    else:  # 4th section (rightmost or bottommost)
        if horizontal:
            ball["vx"] *= increase_factor
        else:
            ball["vy"] *= increase_factor 

def adjust_ball_velocity(ball, paddle_top_y, paddle_length, speed_increment):
    # Determine the bounds of the paddle
    top_bound = paddle_top_y
    bottom_bound = paddle_top_y + paddle_length

    # Check if the ball is within the paddle's vertical range
    if top_bound <= ball["y"] <= bottom_bound:
        # Calculate the paddle's sections
        section_length = paddle_length / 4
        top_section = top_bound + section_length
        bottom_section = bottom_bound - section_length

        # Determine which section the ball hit
        if ball["y"] <= top_section:
            # Top section: Reflect upward
            ball["vy"] = -abs(ball["vy"])  # Ensure it moves upward
        elif ball["y"] >= bottom_section:
            # Bottom section: Reflect downward
            ball["vy"] = abs(ball["vy"])  # Ensure it moves downward
            
        ball["vx"] *= speed_increment  # Optional: Add slight speed increase
        ball["vy"] *= speed_increment

from django.contrib.auth import get_user_model
from matchmaking.models import Player
from django.utils.crypto import get_random_string

User = get_user_model()

def get_or_create_guest_player():
    # Dynamically fetch the Player model
    Player = apps.get_model('matchmaking', 'Player')  # 'matchmaking' is the app label

    guest_username = "Guest"

    # Fetch or create the guest User
    guest_user, created = User.objects.get_or_create(
        username=guest_username,
        defaults={
            "email": "guest@localgame.com",
            "password": get_random_string(10),
            "is_guest": True,  # This assumes your User model has an is_guest field
        }
    )

    # Fetch or create the corresponding Player instance
    guest_player, _ = Player.objects.get_or_create(
        user=guest_user,
        defaults={"nickname": "Guest"}
    )

    return guest_player
     
def get_guest_user_id():
    guest_player = get_or_create_guest_player()
    return guest_player.user.id


# def get_or_create_guest_user():
#     CustomUser = apps.get_model('users', 'CustomUser')  # Dynamically get the model
#     # Create or fetch a default guest user
#     guest_user, created = CustomUser.objects.get_or_create(
#         username="GuestPlayer",
#         defaults={
#             "email": "guest@example.com",  # Placeholder email
#             "avatar": "avatars/default.png",  # Default avatar
#             "is_online": False,  # Prevent marking as online
#             "is_active": False  # Ensure guest cannot log in
#         }
#     )

#     # Handle any updates needed for an existing guest user
#     if not created:
#         # Ensure the fields are consistent in case defaults were updated
#         guest_user.email = "guest@example.com"
#         guest_user.avatar = "avatars/default.png"
#         guest_user.is_online = False
#         guest_user.is_active = False
#         guest_user.save()

#     return guest_user