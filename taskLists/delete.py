import json
import logging
from datetime import datetime
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_list_model import TaskListModel
from models.task_model import TaskModel
from pynamodb.exceptions import UpdateError, QueryError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def delete(event, context):
  """
  tasklistのdeleteFlagをfalseに変更
  また関連するtaskのdeleteFlagもfalseに変更
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_list_id = event['pathParameters']['id']

    # tasklistをget
    try:
      task_list = TaskListModel.get(task_list_id)
    except TaskListModel.DoesNotExist as e:
      logger.exception(e)
      raise errors.NotFound('The taskList does not exist')

    # tasklistを論理削除
    try:
      task_list.logic_delete()
    except UpdateError as e:
      logger.exception(e)
      raise errors.InternalError('Internal server error')

    # 関連するtasksを論理削除
    try:
      tasks = TaskModel.tasks_gsi_taskListId.query(
        task_list_id,
        TaskModel.deleteFlag == False
      )
      print(tasks)
    except QueryError as e:
      logger.exception(e)
      raise errors.InternalError('Internal server error')

    for task in tasks:
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
  
