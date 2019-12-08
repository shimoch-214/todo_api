import json
import logging
import uuid
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.user_model import UserModel
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
    validate_empty(body)
    
    user = UserModel(
      id = str(uuid.uuid1()),
      name = body['name'],
      email = body['email'],
      phoneNumber = body['phoneNumber']
    )
    if not user.validate_email():
      raise errors.BadRequest('Invalid email')
    if not user.validate_phoneNumber():
      raise errors.BadRequest('Invalid phoneNumber')

    # emailの重複がないか
    if not UserModel.email_uniqueness(user):
      raise errors.UnprocessableEntity('This email has been registered')
    # userの保存
    try:
      user.save()
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
          'user': dict(user)
        }
      )
    }

  except errors.BadRequest as e:
    logger.error(e)
    return build_response(e, 400)

  except errors.UnprocessableEntity as e:
    logger.error(e)
    return build_response(e, 409)

  except errors.InternalError as e:
    logger.error(e)
    return build_response(e, 500)

# validations
def validate_attributes(body):
  if "name" not in body or "email" not in body or "phoneNumber" not in body:
    raise errors.BadRequest('"name", "email" and "phoneNumber" attributes are indispensable')

def validate_empty(body):
  if not (body["name"] and body["email"] and body["phoneNumber"]):
    raise errors.BadRequest('"name", "email" and "phoneNumber" attributes are indispensable')
