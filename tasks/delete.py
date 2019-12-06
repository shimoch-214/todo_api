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
from db_util.client import client
import os

# tableの取得
dynamodb = client()
tasks_table = dynamodb.Table(os.environ['tasksTable'])

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def delete(event, context):
  """
  delteFlagをfalseに変更
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_id = event['pathParameters']['id']

    try:
      tasks_table.update_item(
        Key = {
          'id': task_id
        },
        UpdateExpression = 'set deleteFlag = :f',
        ConditionExpression = 'deleteFlag = :now',
        ExpressionAttributeValues = {
          ':f': True,
          ':now': False
        }
      )
    except ClientError as e:
      logger.error(e.response)
      if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
        raise errors.NotFound('The requested task does not exist')
      else:
        raise errors.InternalError('Internal server error')
    
    return {
      'statusCode': 200,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(
        {
          'statusCode': 200
        }
      )
    }
  
  except errors.BadRequest as e:
    logger.error(e)
    return build_response(e, 400)

  except errors.NotFound as e:
    logger.error(e)
    return build_response(e, 404)

  except errors.InternalError as e:
    logger.error(e)
    return build_response(e, 500)
  
  except Exception as e:
    logger.error(e)
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

