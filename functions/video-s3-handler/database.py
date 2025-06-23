import urllib.parse
from pymongo import MongoClient
from config import DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME

username = urllib.parse.quote_plus(DATABASE_USER)
password = urllib.parse.quote_plus(DATABASE_PASSWORD)
mongo_uri = f"mongodb+srv://{username}:{password}@{DATABASE_HOST}/?retryWrites=true&w=majority&appName=mazy-video-tools"

client = MongoClient(mongo_uri)
db = client[DATABASE_NAME]
collection = db['video_events']
