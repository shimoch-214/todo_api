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


def update(event, context):
  """
  updateでの更新対象はemail, name, phoneのみとする
  """
  data = event['body']
  userId = event['path']['id']
  logger.info('headers:' + str(event['headers']))
  logger.info('body:' + str(data))
  logger.info('params:' + str(userId))

  # dataから不要なattributeを削除
  data = { k: v for k, v in data.items() if k in ['email', 'name', 'phone']}
  # email, phone, nameが空であれば削除
  data = { k: v for k, v in data.items() if v}

  if not data:
    logger.error('Invalid Parameters')
    raise errors.CustomError(400, 'Invalid Parameters')

  # dataにupdatedAtを追加
  data['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  UpdateExpression = []
  ExpressionAttributeNames = {}
  ExpressionAttributeValues = {}
  for k, v in data.items():
    UpdateExpression.append('#' + k + '=' + ':' + k[0])
    ExpressionAttributeNames['#' + k] = k
    ExpressionAttributeValues[':' + k[0]] = v
  UpdateExpression = 'set ' + ','.join(UpdateExpression)

  result = table.update_item(
    Key = {
      'id': userId
    },
    UpdateExpression = UpdateExpression,
    ExpressionAttributeNames = ExpressionAttributeNames,
    ExpressionAttributeValues = ExpressionAttributeValues,
    ReturnValues = 'UPDATED_NEW'
  )

  response = {
    'statusCode': 200,
    'id': userId,
    'updatedValues': result['Attributes']
  }
  
  return json.dumps(response)