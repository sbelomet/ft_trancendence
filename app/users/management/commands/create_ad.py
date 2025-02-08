from django.core.management.base import BaseCommand
from users.models import CustomUser

class Command(BaseCommand):
    help = "Create a persistent superuser and test users"

    def handle(self, *args, **kwargs):
        # Create superuser
        if not CustomUser.objects.filter(username="admin").exists():
            CustomUser.objects.create_superuser(
                username="ad",
                email="admin@example.com",
                password="ad"
            )
            self.stdout.write(self.style.SUCCESS("Superuser 'ad' created"))

        # Create test users
        test_users = [
            {"username": "testuser1", "email": "testuser1@example.com", "password": "testpassword1"},
            {"username": "testuser2", "email": "testuser2@example.com", "password": "testpassword2"},
        ]

        for user_data in test_users:
            if not CustomUser.objects.filter(username=user_data["username"]).exists():
                CustomUser.objects.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"]
                )
                self.stdout.write(self.style.SUCCESS(f"User '{user_data['username']}' created"))

        self.stdout.write(self.style.SUCCESS("Persistent users created"))