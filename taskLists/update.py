import json
import logging
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_list_model import TaskListModel
from pynamodb.exceptions import UpdateError

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
    # name, descriptionが空であれば削除
    data = { k: v for k, v in data.items() if v}
    if not data:
      raise errors.BadRequest('Bad request')
    if 'name' in data:
      validation_name(data['name'])
    if 'description' in data:
      validation_name(data['description'])
    task_list_id = event['pathParameters']['id']

    # task_listをget
    try:
      task_list = TaskListModel.get(task_list_id)
    except TaskListModel.DoesNotExist as e:
      logger.error(e)
      raise errors.NotFound('The taskList does not exist')

    # task_listを更新
    actions = []
    if 'name' in data:
      actions.append(TaskListModel.name.set(data['name']))
    if 'description' in data:
      actions.append(TaskListModel.description.set(data['description']))
    try:
      task_list.update(actions = actions)
    except UpdateError as e:
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
          'taskList': dict(task_list)
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

def validation_name(name):
  if type(name) != str:
    raise errors.BadRequest('"name" attribute has to be string')
  
def validation_description(description):
  if type(description) != str:
    raise errors.BadRequest('"description" attribute has to be string')