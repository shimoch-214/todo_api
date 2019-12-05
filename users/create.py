import json
import logging
import uuid
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import sys
sys.path.append("..")
import errors
from errors import build_response
import re
import os

# tableの取得
dynamodb = boto3.resource("dynamodb")
users_table = dynamodb.Table(os.environ['usersTable'])

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
    validate_email(body['email'])
    validate_phone(body['phoneNumber'])

    # emailの重複がないか
    try:
      check = users_table.query(
        IndexName = 'users_gsi_email',
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('email').eq(body['email'])
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if check['Count'] != 0:
      raise errors.UnprocessableEntity('This email has been registered')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user = {
      'id': str(uuid.uuid1()),
      'name': body["name"],
      'email': body["email"],
      'phoneNumber': body["phoneNumber"],
      'createdAt': timestamp,
      'updatedAt': timestamp,
      'deleteFlag': False
    }

    # userの保存
    try:
      users_table.put_item(
        Item = user
      )
    except ClientError as e:
      logger.error(e)
      raise errors.InternalError('Internal server error')

    del user['deleteFlag']
    return {
      'statusCode': 200,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(
        {
          'statusCode': 200,
          'user': user
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

  except Exception as e:
    # その他のエラー
    logger.error(e)
    return {
      'statusCode': 500,
      'headers': {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      'body': json.dumps(
        {
          'statusCode': 500,
          'errorMessage': 'Internal server error'
        }
      )
    }


# validations
def validate_attributes(body):
  if "name" not in body or "email" not in body or "phoneNumber" not in body:
    raise errors.BadRequest('"name", "email" and "phoneNumber" attributes are indispensable')

def validate_empty(body):
  if not (body["name"] and body["email"] and body["phoneNumber"]):
    raise errors.BadRequest('"name", "email" and "phoneNumber" attributes are indispensable')

def validate_email(email):
  if not re.match(r'[A-Za-z0-9\._+]+@[A-Za-z]+\.[A-Za-z]', email):
    raise errors.BadRequest('Invalid email')

def validate_phone(phone_number):
  if not re.match(r'^0\d{9,10}$', phone_number):
    raise errors.BadRequest('Invalid phoneNumber')

