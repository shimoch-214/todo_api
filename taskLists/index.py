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
from errors import build_response
import os

# tableの取得
dynamodb = boto3.resource("dynamodb")
task_lists_table = dynamodb.Table(os.environ['taskListsTable'])

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
      task_lists= task_lists_table.scan(
        FilterExpression = Attr('deleteFlag').eq(False),
        ProjectionExpression = 'id, #nm, description, createdAt, updatedAt',
        ExpressionAttributeNames = {'#nm': 'name'}
      )['Items']
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')

    return {
      'statusCode': 200,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(
        {
          'statusCode': 200,
          'taskLists': task_lists
        }
      )
    }
  
  except errors.InternalError as e:
    logger.error(e)
    return build_response(e, 500)

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