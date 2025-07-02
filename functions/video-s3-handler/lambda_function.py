import json
import uuid
import urllib.parse

from aws_clients import s3_client, sqs_client
from database import collection
from config import logger, INBOUND_QUEUE_URL

def lambda_handler(event, context):
    start_remaining = context.get_remaining_time_in_millis()
    logger.info(f'Lambda start - remaining time: {start_remaining} ms')

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

                    # 1) Extrai bucket e key
                    s3_info = record['s3']
                    bucket = s3_info['bucket']['name']
                    key = urllib.parse.unquote_plus(s3_info['object']['key'])
                    logger.info(f'S3 object: bucket={bucket}, key={key}')

                    # 2) Head object para pegar metadados
                    before_head = context.get_remaining_time_in_millis()
                    logger.info(f'Calling head_object - remaining time: {before_head} ms')
                    response = s3_client.head_object(Bucket=bucket, Key=key)
                    after_head = context.get_remaining_time_in_millis()
                    logger.info(f'head_object done - remaining time: {after_head} ms')

                    # 3) Extrai dos metadados do usuário (caso as chaves estejam com hífen ou underscore)
                    s3_meta = response.get('Metadata', {})
                    video_hash       = s3_meta.get('video-hash')       or s3_meta.get('video_hash')
                    cognito_user_id  = s3_meta.get('cognito-user-id')  or s3_meta.get('cognito_user_id')

                    # 4) Gera video_id como UUID v4
                    video_id = str(uuid.uuid4())

                    # 5) Monta o item no formato desejado
                    timestamp = response['LastModified'].isoformat()
                    item = {
                        'video_id':        video_id,
                        'video_hash':      video_hash,
                        'cognito_user_id': cognito_user_id,
                        'bucket':          bucket,
                        'key':             key,
                        'timestamp':       timestamp
                    }
                    logger.debug(f'Prepared item: {item}')

                    # 6) Insere no MongoDB dentro da transação
                    before_db = context.get_remaining_time_in_millis()
                    logger.info(f'Inserting into DB - remaining time: {before_db} ms')
                    collection.insert_one(item, session=session)
                    after_db = context.get_remaining_time_in_millis()
                    logger.info(f'DB insert complete - remaining time: {after_db} ms')

                    # 7) Enfileira no SQS
                    before_sqs = context.get_remaining_time_in_millis()
                    logger.info(f'Sending to SQS - remaining time: {before_sqs} ms')
                    clean_item = {k: v for k, v in item.items() if k != '_id'}
                    sqs_client.send_message(
                        QueueUrl=INBOUND_QUEUE_URL,
                        MessageBody=json.dumps(clean_item)
                    )
                    after_sqs = context.get_remaining_time_in_millis()
                    logger.info(f'SQS send complete - remaining time: {after_sqs} ms')

                    processed += 1

        except Exception:
            logger.exception('Error during processing, aborting transaction')
            session.abort_transaction()
            raise

    end_remaining = context.get_remaining_time_in_millis()
    logger.info(f'Lambda end - processed {processed} record(s), remaining time: {end_remaining} ms')

    return {
        'statusCode': 200,
        'body': f'Processed {processed} records'
    }
