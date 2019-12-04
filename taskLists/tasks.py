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

# tableの取得
dynamodb = boto3.resource('dynamodb')
task_lists_table = dynamodb.Table('taskListsTable')
tasks_table = dynamodb.Table('tasksTable')

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def tasks(event, context):
  """
  taskListに紐づくtask一覧の取得
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_list_id = event['pathParameters']['id']

    # taskListが存在するか
    try:
      task_list = task_lists_table.query(
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('id').eq(task_list_id)
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if task_list['Count'] == 0:
      raise errors.NotFound('The requested tasklist does not exist')

    # taskの取得
    try:
      tasks = tasks_table.query(
        IndexName = 'tasks_gsi_taskListId',
        FilterExpression = Attr('deleteFlag').eq(False),
        ProjectionExpression = 'id, #nm, description, userIds, createdAt, updatedAt',
        ExpressionAttributeNames = {'#nm': 'name'},
        KeyConditionExpression = Key('taskListId').eq(task_list_id)
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
      'body': json.dumps(
        {
          'statusCode': 200,
          'tasks': tasks
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