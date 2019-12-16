import json
import logging
import uuid
import sys
from datetime import datetime
sys.path.append("..")
import errors
from errors import build_response
from models.user_model import UserModel, InvalidPasswordError
from pynamodb.exceptions import UpdateError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def login(event, context):
  """
  email, passwordを照合
  okであればuserTokenを発行
  """
  try:
    logger.info(event)
    if not event['body']:
      raise errors.BadRequest('Bad request')
    body = json.loads(event['body'])
    # bodyのvalidation
    validate_attributes(body)

    # emailからuserを取得
    user = [_ for _ in UserModel.users_gsi_email.query(
      body['email'],
      UserModel.deleteFlag == False
    )]
    if not user:
      raise errors.BadRequest('The email does not registered')
    else:
      user = user[0]

    # passwordの照合(一旦 == で照合)
    hashed_password = user.password
    user.password = body['password']
    try:
      user.hash_password()
    except InvalidPasswordError as e:
      logger.exception(e)
      raise errors.BadRequest(str(e.with_traceback(sys.exc_info()[2])))
    if hashed_password != user.password:
      raise errors.BadRequest('The email or password is wrong')
    
    # tokenの発行
    user.create_token()
    user.update(actions = [
      UserModel.lastLogin.set(datetime.now()),
      UserModel.userToken.set(user.userToken),
      UserModel.expiry.set(user.expiry)
      ]
    )

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

  except errors.InternalError as e:
    logger.exception(e)
    return build_response(e, 500)


def validate_attributes(body):
  if "email" not in body or "password" not in body:
    raise errors.BadRequest('"email" and "password" attributes are indispensable')


