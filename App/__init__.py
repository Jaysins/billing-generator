__version__ = "0.1.0"
import redis as redi
import settings
import celery

celery_app = celery.Celery("service")

redis = redi.StrictRedis().from_url(settings.REDIS_URL)