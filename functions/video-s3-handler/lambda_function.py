import urllib.parse
from aws_clients import s3_client, sqs_client
from database import collection
from config import logger, INCOMING_QUEUE_URL

def lambda_handler(event, context):
    start_remaining = context.get_remaining_time_in_millis()
    logger.info(f"Lambda start - remaining time: {start_remaining} ms")
    records = event.get('Records', [])
    logger.info(f"Received {len(records)} record(s)")

    processed = 0
    client = collection.database.client
    with client.start_session() as session:
        try:
            logger.info("Starting MongoDB transaction")
            with session.start_transaction():
                for idx, record in enumerate(records, start=1):
                    logger.info(f"[{idx}/{len(records)}] Extracting S3 info")
                    s3_info = record['s3']
                    bucket = s3_info['bucket']['name']
                    key = urllib.parse.unquote_plus(s3_info['object']['key'])
                    logger.info(f"S3 object: bucket={bucket}, key={key}")

                    before_head = context.get_remaining_time_in_millis()
                    logger.info(f"Calling head_object - remaining time: {before_head} ms")
                    response = s3_client.head_object(Bucket=bucket, Key=key)
                    after_head = context.get_remaining_time_in_millis()
                    logger.info(f"head_object done - remaining time: {after_head} ms")

                    metadata = {
                        'bucket': bucket,
                        'key': key,
                        'size': response.get('ContentLength'),
                        'content_type': response.get('ContentType'),
                        'timestamp': response.get('LastModified').isoformat()
                    }
                    logger.debug(f"Metadata collected: {metadata}")

                    before_db = context.get_remaining_time_in_millis()
                    logger.info(f"Inserting into DB - remaining time: {before_db} ms")
                    collection.insert_one(metadata, session=session)
                    after_db = context.get_remaining_time_in_millis()
                    logger.info(f"DB insert complete - remaining time: {after_db} ms")

                    before_sqs = context.get_remaining_time_in_millis()
                    logger.info(f"Sending to SQS - remaining time: {before_sqs} ms")
                    sqs_client.send_message(
                        QueueUrl=INCOMING_QUEUE_URL,
                        MessageBody=str(metadata)
                    )
                    after_sqs = context.get_remaining_time_in_millis()
                    logger.info(f"SQS send complete - remaining time: {after_sqs} ms")

                    processed += 1

        except Exception:
            logger.exception("Error during processing, aborting transaction")
            session.abort_transaction()
            raise

    end_remaining = context.get_remaining_time_in_millis()
    logger.info(f"Lambda end - processed {processed} record(s), remaining time: {end_remaining} ms")

    return {
        'statusCode': 200,
        'body': f'Processed {processed} records'
    }
