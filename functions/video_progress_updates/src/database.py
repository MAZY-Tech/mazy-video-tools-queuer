import urllib.parse
from pymongo import MongoClient
from config import DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME

_client = None

def get_db_collection():
    global _client
    if _client is None:
        username = urllib.parse.quote_plus(DATABASE_USER)
        password = urllib.parse.quote_plus(DATABASE_PASSWORD)
        mongo_uri = f"mongodb+srv://{username}:{password}@{DATABASE_HOST}/?retryWrites=true&w=majority&appName=mazy-video-tools"
        _client = MongoClient(mongo_uri)

    db = _client[DATABASE_NAME]
    collection = db['video_events']
    return collection

collection = get_db_collection

