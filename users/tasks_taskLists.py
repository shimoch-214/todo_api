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
import os

# tableの取得
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['usersTable'])
tasks_table = dynamodb.Table(os.environ['tasksTable'])
task_lists_table = dynamodb.Table(os.environ['taskListsTable'])

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def tasks_taskLists(event, context):
  """
  userが属するtasksおよびtaskListsを返す
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    user_id = event['pathParameters']['id']
    
    # userが存在するか
    try:
      user = users_table.query(
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('id').eq(user_id)
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if user['Count'] == 0:
      raise errors.NotFound('This user does not exist')

    # userが属するtasksを取得
    try:
      tasks = tasks_table.scan(
        FilterExpression = Attr('deleteFlag').eq(False) & Attr('userIds').contains(user_id),
        ProjectionExpression = 'id, #nm, description, taskListId, userIds, done, createdAt, updatedAt',
        ExpressionAttributeNames = {'#nm': 'name'}
      )['Items']
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError

    # taskListIdでグループ化
    tasks_group = {}
    for task in tasks:
      if task['taskListId'] in tasks_group:
        tasks_group[task['taskListId']].append(task)
      else:
        tasks_group[task['taskListId']] = [task]
    
    # taskListsを取得
    task_lists = []
    try:
      for task_list_id in tasks_group.keys():
        task_list = task_lists_table.query(
          FilterExpression = Attr('deleteFlag').eq(False),
          KeyConditionExpression = Key('id').eq(task_list_id),
          ProjectionExpression = 'id, #nm, description, createdAt, updatedAt',
          ExpressionAttributeNames = {'#nm': 'name'}
        )
        task_lists.append(task_list['Items'][0])
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')

    # 結果の整形
    for task_list in task_lists:
      task_list['tasks'] = tasks_group[task_list['id']]

    return {
        'statusCode': 200,
        'headers': {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        },
        'body': json.dumps(
          {
            'statusCode': 200,
            'userId': user_id,
            'taskLists': task_lists
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

