from django.core.management.base import BaseCommand
from chat.models import Message, PrivateMessage

class Command(BaseCommand):
    help = 'Clear all messages from the database'

    def handle(self, *args, **kwargs):
        Message.objects.all().delete()
        PrivateMessage.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared all messages'))