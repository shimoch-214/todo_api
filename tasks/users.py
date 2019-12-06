import json
import logging
import uuid
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import sys
sys.path.append('..')
import errors
from errors import build_response
from db_util.client import client
import os

# tableの取得
dynamodb = client()
users_table = dynamodb.Table(os.environ['usersTable'])
tasks_table = dynamodb.Table(os.environ['tasksTable'])

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def users(event, context):
  """
  taskに所属するuser一覧を返す
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_id = event['pathParameters']['id']

    # taskの取得
    try:
      task = tasks_table.query(
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('id').eq(task_id)
      )
    except ClientError as e:
      logger.info(e.response)
      raise errors.InternalError('Internal server error')
    if task['Count'] == 0:
      raise errors.NotFound('This task does not exist')
    
    # usersの取得
    try:
      users = []
      for user_id in task['Items'][0]['userIds']:
        user = users_table.get_item(Key = {'id': user_id})['Item']
        if not user['deleteFlag']:
          del user['deleteFlag']
          users.append(user)
    except ClientError as e:
      logger.info(e.response)
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
            'taskId': task_id,
            'users': users
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
