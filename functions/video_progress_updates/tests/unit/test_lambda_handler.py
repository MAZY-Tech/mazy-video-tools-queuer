import json
import sys
import os
import json
from datetime import datetime
from unittest.mock import MagicMock
from lambda_function import lambda_handler

FAKE_VIDEO_ID = "video_1"
FAKE_COGNITO_USER_ID = "cognito_user_fake"
FAKE_FILE_NAME = "fake_video.mp4"
FAKE_BUCKET = "meu-bucket-fake"
FAKE_KEY = "zips/my-file.zip"
FAKE_TIMESTAMP = datetime.now().isoformat()
FAKE_NOTIFICATION_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/fake-notification-queue"


def create_sqs_event(video_id, status, progress, zip_info):
    body = {
        "video_id": video_id,
        "status": status,
        "progress": progress,
        "zip": zip_info
    }
    return {
        "Records": [
            {
                "messageId": "fake_message_id",
                "body": json.dumps(body)
            }
        ]
    }


def test_lambda_handler_completed_status(mocker):

    mock_datetime = mocker.patch('lambda_function.datetime', return_value=datetime.fromisoformat(FAKE_TIMESTAMP))
    mock_datetime.now.return_value.isoformat.return_value = FAKE_TIMESTAMP
    mock_collection = MagicMock()
    mock_collection.find_one_and_update.return_value = {
        "video_id": FAKE_VIDEO_ID,
        "cognito_user_id": FAKE_COGNITO_USER_ID,
        "file_name": FAKE_FILE_NAME,
        "status": "COMPLETED",
        "message": ""
    }

    mocker.patch('lambda_function.get_collection', return_value=mock_collection)
    mock_sqs_client = MagicMock()
    mocker.patch('lambda_function.sqs_client', mock_sqs_client)
    mocker.patch('lambda_function.NOTIFICATION_QUEUE_URL', FAKE_NOTIFICATION_QUEUE_URL)

    event = create_sqs_event(
        FAKE_VIDEO_ID,
        "COMPLETED",
        100,
        {"bucket": FAKE_BUCKET, "key": FAKE_KEY}
    )

    response = lambda_handler(event, None)

    mock_collection.find_one_and_update.assert_called_once_with(
        {'video_id': FAKE_VIDEO_ID},
        {'$set': {
            'progress': 100,
            'status': 'COMPLETED',
            'zip': {'bucket': FAKE_BUCKET, 'key': FAKE_KEY},
            'last_update': FAKE_TIMESTAMP
        }},
        return_document=True
    )

    expected_notification_body = {
        'video_id': FAKE_VIDEO_ID,
        'file_name': FAKE_FILE_NAME,
        'cognito_user_id': FAKE_COGNITO_USER_ID,
        'status': 'COMPLETED',
        'message': '',
        'timestamp': FAKE_TIMESTAMP
    }
    mock_sqs_client.send_message.assert_called_once_with(
        QueueUrl=FAKE_NOTIFICATION_QUEUE_URL,
        MessageBody=json.dumps(expected_notification_body)
    )

    assert response['statusCode'] == 200
    assert response['body'] == 'Processed 1 update(s)'