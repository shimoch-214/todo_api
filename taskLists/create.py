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

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def create(event, context):
  """
  taskListを作成
  削除済みレコードは復活させない
  """
  try:
    logger.info(event)
    # validation
    if not event['body']:
      raise errors.BadRequest('Bad request')
    body = json.loads(event['body'])
    validate_attributes(body)
    validate_empty(body)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task_list = {
      'id': str(uuid.uuid1()),
      'name': body['name'],
      'description': body['description'],
      'createdAt': timestamp,
      'updatedAt': timestamp,
      'deleteFlag': False
    }
    # taskListの保存
    try:
      task_lists_table.put_item(
        Item = task_list,
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')

    del task_list['deleteFlag']
    return {
      'statusCode': 200,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(
        {
          'statusCode': 200,
          'taskList': task_list
        }
      )
    }

  except errors.BadRequest as e:
    logger.error(e)
    return build_response(e, 400)

  except errors.InternalError as e:
    logger.error(e)
    return build_response(e, 500)

  except Exception as e:
    # その他のエラー
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


# validations
def validate_attributes(body):
  if not ('name' in body and 'description' in body):
    raise errors.BadRequest('"name" and "description" attributes are indispensable')


def validate_empty(body):
  if not (body['name'] and body['description']):
    raise errors.BadRequest('"name" and "description" attributes are indispensable')