import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_BUCKET = os.environ['S3_BUCKET']
INCOMING_QUEUE_URL = os.environ['INCOMING_QUEUE_URL']
DATABASE_HOST = os.environ['DATABASE_HOST']
DATABASE_PORT = int(os.environ.get('DATABASE_PORT', 27017))
DATABASE_USER = os.environ['DATABASE_USER']
DATABASE_PASSWORD = os.environ['DATABASE_PASSWORD']
DATABASE_NAME = os.environ['DATABASE_NAME']
