import json
from datetime import datetime
from aws_clients import sqs_client
from database import collection
from config import logger, NOTIFICATION_QUEUE_URL
from pymongo import ReturnDocument
from sentry import initialize_sentry

initialize_sentry()


def parse_record(record):
    body = record.get('body')
    logger.info(f"Record body: {body}")
    try:
        return json.loads(body)
    except Exception:
        logger.exception(f"Failed to parse record body: {body}")
        return None

def extract_update_fields(msg):
    fields = {}
    if 'progress' in msg:
        fields['progress'] = msg['progress']
    if 'status' in msg:
        fields['status'] = msg['status']
    if 'zip' in msg:
        fields['zip'] = {
            'bucket': msg['zip'].get('bucket'),
            'key': msg['zip'].get('key')
        }
    return fields

def update_database(video_id, update_fields):
    update_fields['last_update'] = datetime.now().isoformat()
    result = collection.find_one_and_update(
        {'video_id': video_id},
        {'$set': update_fields},
        return_document=ReturnDocument.AFTER
    )
    logger.info(
        f"Updated fields {update_fields} for video_id={video_id}"
    )
    return result

def is_terminal_status(status):
    return status in ('FAILED', 'COMPLETED')

def build_notification_payload(video):
    return {
        'video_id':        video.get('video_id'),
        'file_name':       video.get('file_name'),
        'cognito_user_id': video.get('cognito_user_id'),
        'status':          video.get('status'),
        'message':         video.get('message', ''),
        'timestamp':       datetime.now().isoformat()
    }

def send_notification(notification):
    logger.info(f"Sending notification: {notification}")
    sqs_client.send_message(
        QueueUrl=NOTIFICATION_QUEUE_URL,
        MessageBody=json.dumps(notification)
    )

def lambda_handler(event, context):
    logger.info(f"Lambda start processing event: {event}")
    records = event.get('Records', [])
    logger.info(f"Received {len(records)} record(s)")
    total_updated = 0

    for record in records:
        msg = parse_record(record)
        if not msg:
            continue

        video_id = msg.get('video_id')
        update_fields = extract_update_fields(msg)
        if not update_fields:
            continue

        result = update_database(video_id, update_fields)
        if result:
            total_updated += 1

        status = msg.get('status')
        if result and is_terminal_status(status):
            notification = build_notification_payload(result)
            send_notification(notification)

    logger.info(f"Processed {total_updated} update(s)")
    return {
        'statusCode': 200,
        'body': f'Processed {total_updated} update(s)'
    }
