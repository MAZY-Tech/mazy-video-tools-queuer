import json
from datetime import datetime
from aws_clients import sqs_client
from database import collection
from config import logger, NOTIFICATION_QUEUE_URL


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
    result = collection.update_one(
        {'video_id': video_id},
        {'$set': update_fields}
    )
    logger.info(
        f"Updated fields {update_fields} for video_id={video_id}, "
        f"modified_count={result.modified_count}"
    )
    return result.modified_count

def is_terminal_status(status):
    return status in ('FAILED', 'COMPLETED')

def build_notification_payload(msg):
    return {
        'video_id':        msg.get('video_id'),
        'bucket':          msg.get('zip', {}).get('bucket'),
        'key':             msg.get('zip', {}).get('key'),
        'cognito_user_id': msg.get('cognito_user_id'),
        'status':          msg.get('status'),
        'message':         msg.get('message', ''),
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

        modified = update_database(video_id, update_fields)
        total_updated += modified

        status = msg.get('status')
        if modified and is_terminal_status(status):
            notification = build_notification_payload(msg)
            send_notification(notification)

    logger.info(f"Processed {total_updated} update(s)")
    return {
        'statusCode': 200,
        'body': f'Processed {total_updated} update(s)'
    }
