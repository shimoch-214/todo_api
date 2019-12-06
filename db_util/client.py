import boto3
import os

def client():
  if os.environ['IS_LOCAL']:
    return boto3.resource('dynamodb', endpoint_url = "http://localhost:8000")
  else:
    return boto3.resource('dynamodb')
    