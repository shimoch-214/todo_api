import json
import logging
import uuid
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import sys
sys.path.append("..")
import errors

# tableの取得
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("taskListsTable")

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def index(event, context):
  """
  taskListの一覧を返す
  """
  try:
    logger.info(event)

    try:
      items = table.scan(
        FilterExpression = Attr('deleteFlag').eq(False),
        ProjectionExpression = 'id, #nm, description, createdAt, updatedAt',
        ExpressionAttributeNames = {'#nm': 'name'}
      )['Items']
    except ClientError as e:
      logger.error(e)
      raise errors.InternalError('Internal server error')

    return {
      'statusCode': 200,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(items)
    }


  except Exception as e:
    logger.info(e)
    return {
      'statusCode': 500,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(
        {
          'statusCode': 500,
          'errorMessage': 'Internal server error'
        }
      )
    }