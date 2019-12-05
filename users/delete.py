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

# tableの取得
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('usersTable')
tasks_table = dynamodb.Table('tasksTable')

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def delete(event, context):
  """
  userを削除
  また参加しているtaskのuserIdsから自身を取り除く
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    user_id = event['pathParameters']['id']

    # userの削除
    try:
      users_table.update_item(
        Key = {
          'id': user_id
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
        raise errors.NotFound('This user does not exist')
      else:
        raise errors.InternalError('Internal server error')
    
    # userが参加するtaskのuserIdsからuser_idを削除
    try:
      tasks = tasks_table.scan(
        FilterExpression = Attr('deleteFlag').eq(False) & Attr('userIds').contains(user_id),
        ProjectionExpression = 'id, userIds'
      )['Items']
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError

    for task in tasks:
      task['userIds'] = list(set(task['userIds']) - {user_id})
      try:
        tasks_table.update_item(
          Key = {
            'id': task['id']
          },
          UpdateExpression = 'set userIds = :ui',
          ExpressionAttributeValues = {
            ':ui': task['userIds']
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

