import json
import logging
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_model import TaskModel
from pynamodb.exceptions import UpdateError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def delete(event, context):
  """
  delteFlagをfalseに変更
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_id = event['pathParameters']['id']

    # taskの取得
    try:
      task = TaskModel.get(task_id)
    except TaskModel.DoesNotExist:
      raise errors.NotFound('The task does not exist')

    # taskの削除
    try:
      task.logic_delete()
    except UpdateError as e:
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
          'statusCode': 200
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


