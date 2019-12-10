import json
import logging
import uuid
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.user_model import (
  UserModel, InvalidPhoneNumberError, InvalidEmailError,
  InvalidNameError, InvalidPasswordError
)
from pynamodb.exceptions import PutError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def create(event, context):
  """
  userの作成
  emailは一意に保つ
  """
  try:
    logger.info(event)
    if not event['body']:
      raise errors.BadRequest('Bad request')
    body = json.loads(event['body'])
    # bodyのvalidation
    validate_attributes(body)
    
    user = UserModel(
      id = str(uuid.uuid1()),
      name = body['name'],
      email = body['email'],
      phoneNumber = body['phoneNumber'],
      password = body['password']
    )

    # passwordのhash化
    try:
      user.hash_password()
    except InvalidPasswordError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))

    # tokenの作成
    user.create_token()

    # userの保存
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
        'access-token': user.userToken,
        'expiry': user.get_expiry(),
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

  except errors.UnprocessableEntity as e:
    logger.exception(e)
    return build_response(e, 409)

  except errors.InternalError as e:
    logger.exception(e)
    return build_response(e, 500)

# validations
def validate_attributes(body):
  if "name" not in body or "email" not in body or "phoneNumber" not in body or "password" not in body:
    raise errors.BadRequest('"name", "email","phoneNumber" and "password" attributes are indispensable')

