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
task_lists_table = dynamodb.Table(os.environ['taskListsTable'])
tasks_table = dynamodb.Table(os.environ['tasksTable'])

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def delete(event, context):
  """
  tasklistのdeleteFlagをfalseに変更
  また関連するtaskのdeleteFlagもfalseに変更
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_list_id = event['pathParameters']['id']

    # tasklistをdelete
    try:
      task_lists_table.update_item(
        Key = {
          'id': task_list_id
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
        raise errors.NotFound('This task does not exist')
      else:
        raise errors.InternalError('Internal server error')
    
    # 関連するtaskを取得
    try:
      tasks = tasks_table.query(
        IndexName = 'tasks_gsi_taskListId',
        FilterExpression = Attr('deleteFlag').eq(False),
        ProjectionExpression = 'id',
        KeyConditionExpression = Key('taskListId').eq(task_list_id)
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    task_ids = [task['id'] for task in tasks['Items']]

    # 関連するtaskをdelete
    try:
      for task_id in task_ids:
        tasks_table.update_item(
          Key = {
            'id': task_id
          },
          UpdateExpression = 'set deleteFlag = :f',
          ExpressionAttributeValues = {
            ':f': True,
          }
        )
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

