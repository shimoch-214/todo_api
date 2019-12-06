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
import re
import os

# tableの取得
dynamodb = client()
tasks_table = dynamodb.Table(os.environ['tasksTable'])
users_table = dynamodb.Table(os.environ['usersTable'])

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def add_remove(event, context):
  """
  userをtaskに追加
  """
  try:
    logger.info(event)
    if not (event['pathParameters'] and event['body']):
      raise errors.BadRequest('Bad request')

    data = json.loads(event['body'])
    # dataから不要なattributeを削除
    data = { k: v for k, v in data.items() if k == 'userIds' }
    if not data:
      raise errors.BadRequest('Bad request')
    else:
      if type(data['userIds']) != list:
        raise errors.BadRequest('"userIds" attribute must be array')
    # dataにupdatedAtを追加
    data['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task_id = event['pathParameters']['id']

    # userIdsに含まれるuserが存在しているか
    for user_id in set(data['userIds']):
      try:
        user = users_table.query(
          FilterExpression = Attr('deleteFlag').eq(False),
          KeyConditionExpression = Key('id').eq(user_id)
        )
      except ClientError as e:
        logger.error(e.response)
        raise errors.InternalError('Internal server error')
      if user['Count'] == 0:
        raise errors.BadRequest('The requested user does not exist (userId: {})'.format(user_id))

    # 既存のuserIdsを取得
    try:
      task = tasks_table.query(
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('id').eq(task_id)
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if task['Count'] == 0:
      raise errors.NotFound('The requested task does not exist')
    old_user_ids = set(task['Items'][0]['userIds'])

    # add or removeで和集合 or 差集合
    if re.match('.*/add$', event['resource']):
      new_user_ids = list(old_user_ids | set(data['userIds']))
    else:
      new_user_ids = list(old_user_ids - set(data['userIds']))

    # taskのuserIdsを更新
    try:
      result = tasks_table.update_item(
        Key = {
          'id': task_id
        },
        UpdateExpression = 'set userIds = :new',
        ExpressionAttributeValues = {
          ':new': new_user_ids
        },
        ReturnValues = 'UPDATED_NEW'
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
          'statusCode': 200,
          'task': result['Attributes']
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

