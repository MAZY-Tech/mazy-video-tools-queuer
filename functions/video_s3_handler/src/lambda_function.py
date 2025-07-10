import json
import urllib.parse

from aws_clients import s3_client, sqs_client
from database import collection
from config import logger, INBOUND_QUEUE_URL
from sentry import initialize_sentry

initialize_sentry()


def extract_s3_info(record):
    s3_info = record['s3']
    bucket = s3_info['bucket']['name']
    key = urllib.parse.unquote_plus(s3_info['object']['key'])
    return bucket, key

def get_metadata(bucket, key):
    response = s3_client.head_object(Bucket=bucket, Key=key)
    metadata = response.get('Metadata', {})
    return {
        'video_id': metadata.get('video_id'),
        'video_hash': metadata.get('video_hash'),
        'cognito_user_id': metadata.get('cognito_user_id'),
        'timestamp': response['LastModified'].isoformat()
    }

def build_sqs_message(meta, bucket, key):
    return {
        'video_id': meta['video_id'],
        'video_hash': meta['video_hash'],
        'cognito_user_id': meta['cognito_user_id'],
        'bucket': bucket,
        'key': key,
        'timestamp': meta['timestamp']
    }

def send_to_sqs(message):
    sqs_client.send_message(
        QueueUrl=INBOUND_QUEUE_URL,
        MessageBody=json.dumps(message)
    )

def update_video_status(video_id, session):
    collection.update_one(
        {'video_id': video_id},
        {'$set': {'status': 'QUEUED'}},
        session=session
    )

def lambda_handler(event, context):
    records = event.get('Records', [])
    logger.info(f'Received {len(records)} record(s)')
    processed = 0
    client = collection.database.client

    with client.start_session() as session:
        try:
            logger.info('Starting MongoDB transaction')
            with session.start_transaction():
                for idx, record in enumerate(records, start=1):
                    logger.info(f'[{idx}/{len(records)}] Processing S3 event')
                    bucket, key = extract_s3_info(record)
                    logger.info(f'S3 object: bucket={bucket}, key={key}')

                    meta = get_metadata(bucket, key)
                    message = build_sqs_message(meta, bucket, key)

                    logger.debug(f'Prepared sqs_data: {message}')
                    send_to_sqs(message)
                    update_video_status(meta['video_id'], session)

                    processed += 1

        except Exception:
            logger.exception('Error during processing, aborting transaction')
            session.abort_transaction()
            raise

    logger.info(f'Lambda end - processed {processed} record(s)')
    return {
        'statusCode': 200,
        'body': f'Processed {processed} records'
    }
