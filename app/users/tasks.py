from celery import shared_task
from django.utils.timezone import now
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def clean_expired_blacklisted_tokens():
    """
    Task to clean expired blacklisted tokens older than 2 months.
    """
    try:
        logger.info("Starting clean_expired_blacklisted_tokens task.")

        # Calculate the threshold date (2 months ago)
        threshold_date = now() - timedelta(days=60)

        # Delete tokens created before the threshold date
        expired_tokens = BlacklistedToken.objects.filter(created_at__lt=threshold_date)
        deleted_count, _ = expired_tokens.delete()

        logger.info(f"Successfully deleted {deleted_count} expired blacklisted tokens.")

    except Exception as e:
        logger.exception(f"Error in clean_expired_blacklisted_tokens task: {e}")
