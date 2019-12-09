import json
import logging
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.user_model import UserModel, InvalidEmailError, InvalidPhoneNumberError, InvalidNameError
from pynamodb.exceptions import PutError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def update(event, context):
  """
  userの更新
  updateでの更新対象はemail, name, phoneNumberのみ
  """
  try:
    logger.info(event)
    if not (event['body'] and event['pathParameters']):
      raise errors.BadRequest('Bad request')

    data = json.loads(event['body'])
    # dataから不要なattributeを削除
    data = { k: v for k, v in data.items() if k in ['name', 'email', 'phoneNumber'] }
    if not data:
      raise errors.BadRequest('Bad request')
    user_id = event['pathParameters']['id']

    # userが存在するか
    try:
      user = UserModel.get(user_id)
    except UserModel.DoesNotExist as e:
      raise errors.NotFound('This user does not exist')

    if 'name' in data:
      user.name = data['name']
    if 'email' in data:
      user.email = data['email']
    if 'phoneNumber' in data:
      user.phoneNumber = data['phoneNumber']

    # userの更新
    try:
      user.save()
    except InvalidNameError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
    except InvalidPhoneNumberError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
    except InvalidEmailError as e:
      logger.exception(e)
      if str(e.with_traceback(sys.exc_info()[2])) == 'This email has been registered':
        raise errors.UnprocessableEntity(str(e.with_traceback(sys.exc_info()[2])))
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
      'body': json.dumps(
        {
          'statusCode': 200,
          'user': dict(user)
        }
      )
    }

  except errors.BadRequest as e:
    logger.exception(e)
    return build_response(e, 400)

  except errors.NotFound as e:
    logger.exception(e)
    return build_response(e, 404)

  except errors.UnprocessableEntity as e:
    logger.exception(e)
    return build_response(e, 409)
  
  except errors.InternalError as e:
    logger.exception(e)
    return build_response(e, 500)

