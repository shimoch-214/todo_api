import json
import logging
import sys
sys.path.append('..')
import errors
from errors import build_response
from models.task_model import TaskModel, InvalidUserError
from models.user_model import UserModel

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def users(event, context):
  """
  taskに所属するuser一覧を返す
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
    if not task.userIds:
      task.userIds = []
    # usersの取得
    try:
      users = task.get_users()
    except UserModel.DoesNotExist as e:
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
            'taskId': task_id,
            'users': [dict(user) for user in users]
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
