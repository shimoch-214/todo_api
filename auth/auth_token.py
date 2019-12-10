import json
import logging
from datetime import datetime
from models.user_model import UserModel, InvalidPasswordError

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def auth_token(event, context):
  logger.info(event)
  resource = event['methodArn']
  try:
    token = event['authorizationToken']
  except Exception:
    return auth_response('No Token', 'Deny', resource)
  if not token:
    return auth_response('No Token', 'Deny', resource)

  token_registered = [_ for _ in UserModel.users_gsi_userToken.query(
    token,
    UserModel.expiry > datetime.now()
  )]

  if token_registered:
    token_registered = token_registered[0]
    return auth_response(token_registered.id, 'Allow', resource)
  else:
    return auth_response('Invaid Token', 'Deny', resource)

def auth_response(principal_id, effect, resource):
  return {
    "principalId" : principal_id,
    "policyDocument" : {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Action": "*",
          "Effect": effect,
          "Resource": resource  
        }
      ]
    },
    "context": {
      "authorizedUserId": principal_id
    }
  }