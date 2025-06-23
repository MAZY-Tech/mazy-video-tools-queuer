import json
from datetime import datetime
from database import collection
from config import logger

def lambda_handler(event, context):
    logger.info(f"Lambda start processing event: {event}")
    records = event.get('Records', [])
    logger.info(f"Received {len(records)} record(s)")
    updated = 0

    for record in records:
        logger.info(f"Record body: {record.get('body')}")
        body = record.get('body')
        try:
            msg = json.loads(body)
        except Exception:
            logger.exception(f"Failed to parse record body: {body}")
            continue

        filter_criteria = {
            'bucket': msg.get('bucket'),
            'key': msg.get('key'),
        }

        update_fields = {}
        if 'progress' in msg:
            update_fields['progress'] = msg['progress']
        if 'status' in msg:
            update_fields['status'] = msg['status']
        if 'zip_bucket' in msg and 'zip_key' in msg:
            update_fields['zip'] = {
                'bucket': msg['zip_bucket'],
                'key': msg['zip_key']
            }

        if update_fields:
            update_fields['last_update'] = datetime.utcnow().isoformat()
            result = collection.update_one(filter_criteria, {'$set': update_fields})
            logger.info(f"Updated fields {update_fields} for {filter_criteria}, modified_count: {result.modified_count}")
            logger.info(f"Updated {result.modified_count} document(s) for {filter_criteria}")
            updated += result.modified_count

    logger.info(f"Processed {updated} update(s)")
    return {
        'statusCode': 200,
        'body': f'Processed {updated} update(s)'
    }
