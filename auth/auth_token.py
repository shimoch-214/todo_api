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
    return failed_response(resource)
  if not token:
    return failed_response(resource)

  token_registered = [_ for _ in UserModel.users_gsi_userToken.query(
    token,
    UserModel.expiry > datetime.now()
  )]

  if token_registered:
    token_registered = token_registered[0]
    return successed_response(token_registered.id, resource)
  else:
    return failed_response(resource)

def successed_response(principal_id, resource):
  return {
    "principalId" : principal_id,
    "policyDocument" : {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Action": "*",
          "Effect": 'Allow',
          "Resource": resource  
        }
      ]
    },
    "context": {
      "authorizedUserId": principal_id
    }
  }

def failed_response(resource):
  return {
    "principalId" : 'failed',
    "policyDocument" : {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Action": "*",
          "Effect": 'Deny',
          "Resource": resource  
        }
      ]
    },
    "context": {
      'message': 'access denied'
    }
  }