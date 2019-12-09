import json
import logging
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_model import TaskModel, InvalidNameError, InvalidDescriptionError
from pynamodb.exceptions import PutError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def update(event, context):
  """
  taskをupdate
  nameおよびdescription
  """
  try:
    logger.info(event)
    if not (event['body'] and event['pathParameters']):
      raise errors.BadRequest('Bad request')
    
    data = json.loads(event['body'])
    # dataから不要なattributeを削除
    data = { k: v for k, v in data.items() if k in ['name', 'description'] }
    if not data:
      raise errors.BadRequest('Bad request')
    task_id = event['pathParameters']['id']

    # taskの取得
    try:
      task = TaskModel.get(task_id)
    except TaskModel.DoesNotExist:
      raise errors.NotFound('The task does not exist')
    if 'name' in data:
      task.name = data['name']
    if 'description' in data:
      task.description = data['description']
    if not task.userIds:
      task.userIds = []

    try:
      task.save()
    except InvalidNameError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
    except InvalidDescriptionError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
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
          'task': dict(task)
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


