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

# tableの取得
dynamodb = boto3.resource("dynamodb")
users_table = dynamodb.Table("usersTable")

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
    # name, email, phoneNumberが空であれば削除
    data = { k: v for k, v in data.items() if v }
    if not data:
      raise errors.BadRequest('Bad request')
    if 'email' in data:
      validate_email(data['email'])
    if 'phoneNumber' in data:
      validate_phone(data['phoneNumber'])
    # dataにupdatedAtを追加
    data['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_id = event['pathParameters']['id']

    # userが存在するか
    try:
      user = users_table.query(
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('id').eq(user_id)
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if user['Count'] == 0:
      raise errors.NotFound('This user does not exist')

    # 変更後のemailが他のemailと競合しないか
    try:
      check = users_table.query(
        IndexName = 'users_gsi_email',
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('email').eq(data['email'])
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if check['Count'] != 0 and check['Items'][0]['id'] != user_id:
      raise errors.UnprocessableEntity('This email has been registered')

    # userの更新
    UpdateExpression = []
    ExpressionAttributeNames = {}
    ExpressionAttributeValues = {}
    for k, v in data.items():
      UpdateExpression.append('#' + k + '=' + ':' + k[0])
      ExpressionAttributeNames['#' + k] = k
      ExpressionAttributeValues[':' + k[0]] = v
    UpdateExpression = 'set ' + ','.join(UpdateExpression)
    try:
      result = users_table.update_item(
        Key = {
          'id': user_id
        },
        UpdateExpression = UpdateExpression,
        ExpressionAttributeNames = ExpressionAttributeNames,
        ExpressionAttributeValues = ExpressionAttributeValues,
        ReturnValues = 'UPDATED_NEW'
      )
    except ClientError as e:
      logger.error(e.response)
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
          'user': result['Attributes']
        }
      )
    }

  except errors.BadRequest as e:
    logger.error(e)
    return build_response(e, 400)

  except errors.NotFound as e:
    logger.error(e)
    return build_response(e, 404)

  except errors.UnprocessableEntity as e:
    logger.error(e)
    return build_response(e, 409)
  
  except errors.InternalError as e:
    logger.error(e)
    return build_response(e, 500)

  except Exception as e:
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


def validate_email(email):
  if not re.match(r'[A-Za-z0-9\._+]+@[A-Za-z]+\.[A-Za-z]', email):
    raise errors.BadRequest('Invalid email')

def validate_phone(phone_number):
  if not re.match(r'^0\d{9,10}$', phone_number):
    raise errors.BadRequest('Invalid phoneNumber')