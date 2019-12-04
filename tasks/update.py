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

# tableの取得
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("tasksTable")

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def update(event, context):
  """
  taskをupdate
  nameおよびdescription
  """
  try:
    logger.info(event)
    if not (event['body'] and event['pathParameters']):
      raise errors.BadRequest('Bad request')
    
    data = json.loads(event['body'])
    # dataから不要なattributeを削除
    data = { k: v for k, v in data.items() if k in ['name', 'description'] }
    # name, descriptionが空であれば削除
    data = { k: v for k, v in data.items() if v }
    if not data:
      raise errors.BadRequest('Bad request')
    # dataにupdatedAtを追加
    data['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task_id = event['pathParameters']['id']

    UpdateExpression = []
    ExpressionAttributeNames = {}
    ExpressionAttributeValues = {}
    for k, v in data.items():
      UpdateExpression.append('#' + k + '=' + ':' + k[0])
      ExpressionAttributeNames['#' + k] = k
      ExpressionAttributeValues[':' + k[0]] = v
    UpdateExpression = 'set ' + ','.join(UpdateExpression)
    ConditionExpression = 'deleteFlag = :flag'
    ExpressionAttributeValues[':flag'] = False
    try:
      result = table.update_item(
        Key = {
          'id': task_id
        },
        UpdateExpression = UpdateExpression,
        ConditionExpression = ConditionExpression,
        ExpressionAttributeNames = ExpressionAttributeNames,
        ExpressionAttributeValues = ExpressionAttributeValues,
        ReturnValues = 'UPDATED_NEW'
      )
    except ClientError as e:
      logger.error(e.response)
      if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
        raise errors.NotFound('The requested task does not exist')
      else:
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
          'task': result['Attributes']
        }
      )    
    }

  except errors.BadRequest as e:
    logger.error(e)
    return build_response(e, 400)

  except errors.NotFound as e:
    logger.error(e)
    return build_response(e, 404)
  
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