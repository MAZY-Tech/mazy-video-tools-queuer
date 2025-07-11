import boto3
from config import AWS_REGION

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs', region_name=AWS_REGION)
