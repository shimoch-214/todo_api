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
table = dynamodb.Table("taskListsTable")

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def delete(event, context):
  """
  deleteFlagを追加
  deletedAtを追加
  関連するtaskをdelete
  """
  try:
    logger.info(event)
    # pathにidが含まれているか
    if not event['pathParameters']:
      raise errors.BadRequest('Bad Request')
    taskListId = event['pathParameters']['id']
    taskList = table.get_item(
      Key = {
        'id': taskListId
      }
    )['Item']


    return {
      'statusCode': 200,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps(taskList)
    }


  except Exception as e:
    logger.error(e)
    return {
      'statusCode': 500,
      'headers': {
        'Content-Type': 'text/plain'
      },
      'body': 'Internal server error'
    }