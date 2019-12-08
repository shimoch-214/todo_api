import json
import logging
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_list_model import TaskListModel
from pynamodb.exceptions import PutError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def update(event, context):
  """
  taskListの更新
  nameおよびdescription
  """
  try:
    logger.info(event)
    if not (event['body'] and event['pathParameters']):
      raise errors.BadRequest('Bad request')
    
    data = json.loads(event['body'])
    # dataから不要なattributeを削除
    data = { k: v for k, v in data.items() if k in ['name', 'description']}
    if not data:
      raise errors.BadRequest('Bad request')
    task_list_id = event['pathParameters']['id']

    # task_listをget
    try:
      task_list = TaskListModel.get(task_list_id)
    except TaskListModel.DoesNotExist as e:
      raise errors.NotFound('This taskList does not exist')
    # task_listを更新
    if 'name' in data:
      task_list.name = data['name']
    if 'description' in data:
      task_list.description = data['description']
    try:
      task_list.save()
    except TypeError as e:
      logger.exception(e)
      raise errors.BadRequest('"name" and "description" attributes are string')
    except ValueError as e:
      logger.exception(e)
      raise errors.BadRequest('"name" and "description" attributes must not be empty')
    except PutError as e:
      logger.exception(e)
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
          'taskList': dict(task_list)
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
