import json
import logging
import uuid
import sys
sys.path.append('..')
import errors
from errors import build_response
from models.user_model import UserModel
from models.task_model import TaskModel
from models.task_list_model import TaskListModel
from pynamodb.exceptions import UpdateError, ScanError, GetError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def tasks_taskLists(event, context):
  """
  userが属するtasksおよびtaskListsを返す
  """
  try:
    logger.info(event)
    if not event['pathParameters']:
      raise errors.BadRequest('Bad request')
    user_id = event['pathParameters']['id']
    
    # userを取得
    try:
      user = UserModel.get(user_id)
    except UserModel.DoesNotExist:
      raise errors.NotFound('The user does not exist')
    
    # userの参加するtasksを取得
    try:
      tasks = user.get_tasks()
    except ScanError as e:
      logger.exception(e)
      raise errors.InternalError('Internal server error')

    # taskListIdでグループ化
    tasks_group = {}
    for task in tasks:
      if task.taskListId in tasks_group:
        tasks_group[task.taskListId].append(task)
      else:
        tasks_group[task.taskListId] = [task]
    
    # taskListsを取得
    task_lists = []
    for task_list_id in tasks_group.keys():
      try:
        task_list = TaskListModel.get(task_list_id)
      except TaskListModel.DoesNotExist as e:
        logger.exception(e)
        continue
      except GetError as e:
        logger.exception(e)
      task_lists.append(task_list)

    # 結果の整形
    task_lists = [dict(task_list) for task_list in task_lists]
    for task_list in task_lists:
      task_list['tasks'] = [dict(task) for task in tasks_group[task_list['id']]]

    return {
        'statusCode': 200,
        'headers': {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        },
        'body': json.dumps(
          {
            'statusCode': 200,
            'userId': user_id,
            'taskLists': task_lists
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


