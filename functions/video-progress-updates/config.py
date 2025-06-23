import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DATABASE_HOST = os.environ['DATABASE_HOST']
DATABASE_PORT = int(os.environ.get('DATABASE_PORT', 27017))
DATABASE_USER = os.environ['DATABASE_USER']
DATABASE_PASSWORD = os.environ['DATABASE_PASSWORD']
DATABASE_NAME = os.environ['DATABASE_NAME']
