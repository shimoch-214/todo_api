import json
import logging
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_list_model import TaskListModel
from models.task_model import TaskModel
from pynamodb.exceptions import QueryError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def tasks(event, context):
  """
  taskListに紐づくtask一覧の取得
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    task_list_id = event['pathParameters']['id']

    # taskListが存在するか
    try:
      task_list = TaskListModel.get(task_list_id)
    except TaskListModel.DoesNotExist as e:
      logger.exception(e)
      raise errors.NotFound('The taskList does not exist')

    # tasksの取得
    try:
      tasks = TaskModel.tasks_gsi_taskListId.query(
        task_list_id,
        TaskModel.deleteFlag == False
      )
    except QueryError as e:
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
          'taskList': task_list_id,
          'tasks': [dict(task) for task in tasks]
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