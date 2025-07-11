import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION        = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET         = os.getenv('S3_BUCKET')
DATABASE_HOST     = os.getenv('DATABASE_HOST')
DATABASE_PORT     = int(os.getenv('DATABASE_PORT', 27017))
DATABASE_USER     = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME     = os.getenv('DATABASE_NAME')
INBOUND_QUEUE_URL = os.getenv('INBOUND_QUEUE_URL')
SENTRY_DSN        = os.getenv('SENTRY_DSN')
