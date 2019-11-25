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

def create(event, context):
  user = event["body"]
  logger.info("headers:" + str(event["headers"]))
  logger.info("body:" + str(event["body"]))

  # bodyのvalidation
  validate_attributes(user)
  validate_empty(user)

  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  item = {
    'id': str(uuid.uuid1()),
    'name': user["name"],
    'email': user["email"],
    'phone': user["phone"],
    'createdAt': timestamp,
    'updatedAt': timestamp,
    'deleteFlag': False
  }

  table.put_item(Item = item)

  response = {
    'statusCode': 200,
    'headers': {
      'Content-Type': 'application/json',
      'Accept-Charset': 'UTF-8'
    },
    'body': {
      'id': item['id'],
    }
  }

  return json.dumps(response)

# validations
def validate_attributes(user):
  if "name" not in user or "email" not in user or "phone" not in user:
    logger.error("Invalid parameter")
    raise errors.CustomError(400, "Invalid Parameter")


def validate_empty(user):
  if not (user["name"] and user["email"] and user["phone"]):
    logger.error("invalid parameter")
    raise errors.CustomError(400, "Invalid Parameter")