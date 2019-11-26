import json
import logging
import uuid
from datetime import datetime
import boto3
import sys
sys.path.append("..")
import errors

# tableの取得
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("usersTable")

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def delete(event, context):
  """
  delteFlagをfalseに変更
  deletedAtを追加
  """
  userId = event['path']['id']
  logger.info('headers:' + str(event['headers']))
  logger.info('params:' + str(userId))

  result = table.update_item(
    Key = {
      'id': userId
    },
    UpdateExpression = 'set #flag = :f',
    ConditionExpression = '#flag = :done',
    ExpressionAttributeNames = {
      '#flag': 'deleteFlag'
    },
    ExpressionAttributeValues = {
      ':f': True,
      ':done': False
    },
    ReturnValues = 'UPDATED_NEW'
  )

  response = {
    'statusCode': 200,
    'id': userId
  }

  return json.dumps(response)