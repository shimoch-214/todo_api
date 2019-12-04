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
users_table = dynamodb.Table('usersTable')

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def create(event, context):
  """
  taskを作成
  name, descriptionは必須
  userIdsは任意
  """
  try:
    logger.info(event)
    if not (event['body']):
      raise errors.BadRequest('Bad request')
    body = json.loads(event['body'])
    validate_attributes(body)
    validate_empty(body)
    if not 'userIds' in body:
      body['userIds'] = []

    # taskListが存在しているか
    try:
      task_list = task_lists_table.query(
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('id').eq(body['taskListId'])
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if task_list['Count'] == 0:
      raise errors.BadRequest('The requested tasklist does not exist')

    # userIdsに含まれるユーザーが存在するか
    if body['userIds']:
      for userId in body['userIds']:
        try:
          user = users_table.query(
            FilterExpression = Attr('deleteFlag').eq(False),
            KeyConditionExpression = Key('id').eq(userId)
          )
        except ClientError as e:
          logger.error(e.response)
          raise errors.InternalError('Internal server error')
        if user['Count'] == 0:
          raise errors.BadRequest('The requested user does not exist (userId: {})'.format(userId))


    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task = {
      'id': str(uuid.uuid1()),
      'name': body['name'],
      'description': body['description'],
      'taskListId': body['taskListId'],
      'userIds': body['userIds'],
      'createdAt': timestamp,
      'updatedAt': timestamp,
      'deleteFlag': False,
      'done': False
    }

    # taskの保存
    try:
      tasks_table.put_item(
        Item = task
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')

    del task['deleteFlag']
    return {
      'statusCode': 200,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps({
        'statusCode': 200,
        'task': task
      })
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
      'body': json.dumps({'errorMessage': 'Internal server error'})
    }

# validations
def validate_attributes(body):
  if not ('name' in body and 'description' in body and 'taskListId' in body):
    raise errors.BadRequest('"name", "description" and "taskListId" attributes are indispensable')

def validate_empty(body):
  if not (body['name'] and body['description'] and body['taskListId']):
    raise errors.BadRequest('"name", "description" and "taskListId" attributes are indispensable')

def validate_userIds(body):
  if 'userIds' in body:
    if type(body['userIds'] != list):
      raise errors.BadRequest('"userIds" attribute must be array')
