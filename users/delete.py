import json
import logging
import sys
sys.path.append('..')
import errors
from errors import build_response
from models.user_model import UserModel
from models.task_model import TaskModel
from pynamodb.exceptions import UpdateError, ScanError

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

    # userの取得
    try:
      user = UserModel.get(user_id)
    except UserModel.DoesNotExist:
      raise errors.NotFound('The user does not exist')

    # userが参加するtaskの取得
    try:
      tasks = user.get_tasks()
    except ScanError as e:
      logger.exception(e)
      raise errors.InternalError('Internal server error')

    # userが参加するtaskのuserIdsからuser_idを削除
    for task in tasks:
      try:
        task.update(
          [TaskModel.userIds.delete([user_id])]
        )
      except UpdateError as e:
        logger.exception(e)
        raise errors.InternalError('Internal server error')
    
    # userを削除
    try:
      user.logic_delete()
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

