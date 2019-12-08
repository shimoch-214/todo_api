import json
import logging
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_list_model import TaskListModel
from pynamodb.exceptions import ScanError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def index(event, context):
  """
  taskListの一覧を返す
  """
  try:
    logger.info(event)
    try:
      task_lists = TaskListModel.scan(TaskListModel.deleteFlag == False)
    except ScanError as e:
      logger.error(e)
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
          'taskLists': [dict(task_list) for task_list in task_lists]
        }
      )
    }
  
  except errors.InternalError as e:
    logger.error(e)
    return build_response(e, 500)
