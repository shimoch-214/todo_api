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
from models.task_model import TaskModel, InvalidUserError
from pynamodb.exceptions import UpdateError
import re

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
    task_id = event['pathParameters']['id']
    user_ids = data['userIds']

    # taskの取得
    try:
      task = TaskModel.get(task_id)
    except TaskModel.DoesNotExist:
      raise errors.NotFound('The task does not exist')

    # add or remove
    if re.match('.*/add$', event['resource']):
      flag = True
    else:
      flag = False

    # taskのuserIdsを更新
    try:
      task.user_ids_update(user_ids, flag)
    except InvalidUserError as e:
      logger.exception(e)
      raise errors.NotFound(str(e.with_traceback(sys.exc_info()[2])))
    except UpdateError as e:
      logger.exception(e)
      raise errors.InternalError('Internal server error')
    task = TaskModel.get(task_id)

    return {
      'statusCode': 200,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(
        {
          'statusCode': 200,
          'task': dict(task)
        }
      )    
    }

  except errors.BadRequest as e:
    logger.exception(e)
    return build_response(e, 400)

  except errors.NotFound as e:
    logger.exception(e)
    return build_response(e, 404)
  
  except errors.InternalError as e:
    logger.exception(e)
    return build_response(e, 500)

  except Exception as e:
    logger.exception(e)
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

