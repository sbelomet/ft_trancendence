import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from pathlib import Path

# Set the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_ROOT = BASE_DIR.parent

# Determine which .env file to load based on an environment variable or default
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')  # default to 'dev' if not set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hello_django.settings')

if ENVIRONMENT == 'prod':
    load_dotenv(PROJECT_ROOT / '.env.prod')
elif ENVIRONMENT == 'dev':
    load_dotenv(PROJECT_ROOT / '.env.dev')
else:
    load_dotenv(PROJECT_ROOT / '.env')


SECRET_KEY = os.environ.get('SECRET_KEY')


app = Celery('hello_django')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    'launch-tournaments-every-minute': {
        'task': 'matchmaking.tasks.launch_tournaments',
        #'schedule': timedelta(seconds=30),
        'schedule': crontab(),  # runs every minute
    },
    'clean-blacklisted-tokens-every-2-months': {
        'task': 'users.tasks.clean_expired_blacklisted_tokens',
        'schedule': crontab(0, 0, 1, '*/2'),  # Runs at midnight on the first day of every 2nd month
    },
}