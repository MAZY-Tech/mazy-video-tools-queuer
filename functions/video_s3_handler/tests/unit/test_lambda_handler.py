import json
from datetime import datetime
from unittest.mock import MagicMock
from lambda_function import lambda_handler

FAKE_BUCKET = "meu-bucket-fake"
FAKE_KEY = "videos/fake_video.mp4"
FAKE_VIDEO_ID = "video_123"
FAKE_VIDEO_HASH = "hash_abc"
FAKE_COGNITO_USER_ID = "user_xyz"
FAKE_TIMESTAMP = datetime.now().isoformat()
FAKE_INBOUND_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/inbound-queue"


def create_s3_event(bucket, key):
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key}
                }
            }
        ]
    }


def test_lambda_handler_successful_flow(mocker):

    mock_s3_client = mocker.patch('lambda_function.s3_client')
    mock_s3_client.head_object.return_value = {
        'Metadata': {
            'video_id': FAKE_VIDEO_ID,
            'video_hash': FAKE_VIDEO_HASH,
            'cognito_user_id': FAKE_COGNITO_USER_ID
        },
        'LastModified': datetime.fromisoformat(FAKE_TIMESTAMP)
    }

    # Mock SQS
    mock_sqs_client = mocker.patch('lambda_function.sqs_client')
    mocker.patch('lambda_function.INBOUND_QUEUE_URL', FAKE_INBOUND_QUEUE_URL)

    # Mock Mongo collection and session
    mock_collection = MagicMock()
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_database = MagicMock()
    mock_database.client = mock_client
    mock_client.start_session.return_value.__enter__.return_value = mock_session
    mocker.patch('lambda_function.collection', mock_collection)
    mock_collection.database = mock_database

    event = create_s3_event(FAKE_BUCKET, FAKE_KEY)
    response = lambda_handler(event, None)

    mock_s3_client.head_object.assert_called_once_with(Bucket=FAKE_BUCKET, Key=FAKE_KEY)
    mock_sqs_client.send_message.assert_called_once_with(
        QueueUrl=FAKE_INBOUND_QUEUE_URL,
        MessageBody=json.dumps({
            'video_id': FAKE_VIDEO_ID,
            'video_hash': FAKE_VIDEO_HASH,
            'cognito_user_id': FAKE_COGNITO_USER_ID,
            'bucket': FAKE_BUCKET,
            'key': FAKE_KEY,
            'timestamp': FAKE_TIMESTAMP
        })
    )
    mock_collection.update_one.assert_called_once_with(
        {'video_id': FAKE_VIDEO_ID},
        {'$set': {'status': 'QUEUED'}},
        session=mock_session
    )

    assert response['statusCode'] == 200
    assert response['body'] == 'Processed 1 records'
