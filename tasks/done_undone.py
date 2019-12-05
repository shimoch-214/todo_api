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
import re
import os

# tableの取得
dynamodb = boto3.resource('dynamodb')
tasks_table = dynamodb.Table(os.environ['tasksTable'])

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def done_undone(event, context):
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_id = event['pathParameters']['id']

    # done or undone で ture or false
    if re.match('.*/done$', event['resource']):
      check = True
    else:
      check = False

    # taskを更新
    try:
      tasks_table.update_item(
        Key = {
          'id': task_id
        },
        UpdateExpression = 'set done = :d',
        ConditionExpression = 'deleteFlag = :flag',
        ExpressionAttributeValues = {
          ':d': check,
          ':flag': False
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

