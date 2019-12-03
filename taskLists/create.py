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

# tableの取得
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("taskListsTable")

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def create(event, context):
  """
  taskListを作成
  nameは重複なし
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
  
    # 同名のtaskListが存在するか
    try:
      check = table.query(
        IndexName = 'taskLists_gsi_name',
        KeyConditionExpression = Key('name').eq(task_list['name'])
      )
    except ClientError as e:
      logger.error(e)
      raise errors.InternalError('Internal server Error')
    if check['Count'] != 0:
      if not check['Items'][0]['deleteFlag']:
        raise errors.UnprocessableEntity('The name attribute conflicts with another item')

    # taskListの保存
    try:
      table.put_item(
        Item = task_list,
      )
    except ClientError as e:
      raise errors.InternalError('Internal server error')


    response = {
      'statusCode': 200,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({
        'statusCode': 200,
        'taskListId': task_list['id']
      })
    }
    return response

  except errors.BadRequest as e:
    logger.error(e)
    return {
      'statusCode': 400,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': str(e.with_traceback(sys.exc_info()[2]))})
    }

  except errors.UnprocessableEntity as e:
    logger.error(e)
    return {
      'statusCode': 409,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': str(e.with_traceback(sys.exc_info()[2]))})
    }

  except errors.InternalError as e:
    logger.error(e)
    return {
      'statusCode': 500,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': str(e.with_traceback(sys.exc_info()[2]))})
    }

  except Exception as e:
    # その他のエラー
    logger.error(e)
    return {
      'statusCode': 500,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': 'Internal server error'})
    }


# validations
def validate_attributes(body):
  if not ('name' in body and 'description' in body):
    raise errors.BadRequest('Bad request')


def validate_empty(body):
  if not (body['name'] and body['description']):
    raise errors.BadRequest('Bad request')