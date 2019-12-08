import json
import logging
import uuid
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_list_model import TaskListModel
from pynamodb.exceptions import PutError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def create(event, context):
  """
  taskListを作成
  削除済みレコードは復活させない
  """
  try:
    logger.info(event)
    # validation
    if not event['body']:
      raise errors.BadRequest('Bad request')
    body = json.loads(event['body'])
    validate_attributes(body)
    validate_empty(body)

    task_list = TaskListModel(
      str(uuid.uuid1()),
      name = body['name'],
      description = body['description']
    )
    # taskListの保存
    try:
      task_list.save()
    except PutError as e:
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

  except errors.InternalError as e:
    logger.error(e)
    return build_response(e, 500)



# validations
def validate_attributes(body):
  if not ('name' in body and 'description' in body):
    raise errors.BadRequest('"name" and "description" attributes are indispensable')


def validate_empty(body):
  if not (body['name'] and body['description']):
    raise errors.BadRequest('"name" and "description" attributes are indispensable')