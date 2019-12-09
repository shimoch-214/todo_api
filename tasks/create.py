import json
import logging
import uuid
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.task_model import TaskModel, InvalidNameError, InvalidDescriptionError, InvalidTaskListError, InvalidUserError
from pynamodb.exceptions import PutError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def create(event, context):
  """
  taskを作成
  name, descriptionは必須
  userIdsは任意
  """
  try:
    logger.info(event)
    if not (event['body']):
      raise errors.BadRequest('Bad request')
    body = json.loads(event['body'])
    validate_attributes(body)
    if not 'userIds' in body:
      body['userIds'] = []

    task = TaskModel(
      id = str(uuid.uuid1()),
      name = body['name'],
      description = body['description'],
      taskListId = body['taskListId'],
      userIds = body['userIds']
    )

    # taskの保存
    try:
      task.save()
    except InvalidNameError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
    except InvalidDescriptionError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
    except InvalidTaskListError as e:
      logger.exception(e)
      if str(e.with_traceback(sys.exc_info()[2])) == 'The taskList does not exist':
        raise errors.NotFound(str(e.with_traceback(sys.exc_info()[2])))
      else:
        raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
    except InvalidUserError as e:
      logger.exception(e)
      if str(e.with_traceback(sys.exc_info()[2])) == 'The userIds contains a invalid userId does not exist':
        raise errors.NotFound(str(e.with_traceback(sys.exc_info()[2])))
      else:
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
      'body': json.dumps({
        'statusCode': 200,
        'task': dict(task)
      })
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

# validations
def validate_attributes(body):
  if not ('name' in body and 'description' in body and 'taskListId' in body):
    raise errors.BadRequest('"name", "description" and "taskListId" attributes are indispensable')

