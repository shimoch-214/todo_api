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

# tableの取得
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("taskListsTable")

# logの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def update(event, context):
  """
  taskListの更新
  nameおよびdescription
  """
  try:
    logger.info(event)
    if not (event['body'] and event['pathParameters']):
      raise errors.BadRequest('Bad request')
    
    data = json.loads(event['body'])
    # dataから不要なattributeを削除
    data = { k: v for k, v in data.items() if k in ['name', 'description']}
    # name, descriptionが空であれば削除
    data = { k: v for k, v in data.items() if v}
    if not data:
      raise errors.BadRequest('Bad request')
    # dataにupdatedAtを追加
    data['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task_list_id = event['pathParameters']['id']

    # 変更前のdataを取得
    try:
      old_data = table.query(
        FilterExpression = Attr('deleteFlag').eq(False),
        KeyConditionExpression = Key('id').eq(task_list_id)
      )
    except ClientError as e:
      logger.error(e.response)
      raise errors.InternalError('Internal server error')
    if old_data['Count'] == 0:
      raise errors.NotFound('Not found')

    # 変更後のnameが他のitemと競合するか
    if 'name' in data:
      try:
        check = table.query(
          IndexName = 'taskLists_gsi_name',
          FilterExpression = Attr('deleteFlag').eq(False),
          KeyConditionExpression = Key('name').eq(data['name'])
        )
      except ClientError as e:
        logger.error(e.response)
        raise errors.InternalError('Internal server error')
      if check['Count'] != 0:
        if check['Items'][0]['name'] == old_data['Items'][0]['name'] and check['Items'][0]['id'] != task_list_id:
          raise errors.UnprocessableEntity('The name attribute conflicts with another item')

    logger.info('hoge')
    UpdateExpression = []
    ExpressionAttributeNames = {}
    ExpressionAttributeValues = {}
    for k, v in data.items():
      UpdateExpression.append('#' + k + '=' + ':' + k[0])
      ExpressionAttributeNames['#' + k] = k
      ExpressionAttributeValues[':' + k[0]] = v
    UpdateExpression = 'set ' + ','.join(UpdateExpression)
    try:
      result = table.update_item(
        Key = {
          'id': task_list_id
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
        'Content-Type': 'application/json'
      },
      'body': json.dumps(result['Attributes'])
    }

  except errors.NotFound as e:
    logger.error(e)
    return {
      'statusCode': 404,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': str(e.with_traceback(sys.exc_info()[2]))})
    }

  except errors.UnprocessableEntity as e:
    logger.error(e)
    return {
      'statusCode': 409,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': str(e.with_traceback(sys.exc_info()[2]))})
    }
  
  except errors.InternalError as e:
    logger.error(e)
    return {
      'statusCode': 500,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': str(e.with_traceback(sys.exc_info()[2]))})
    }

  except Exception as e:
    logger.error(e)
    return {
      'statusCode': 500,
      'headers': {
        'Content-Type': 'application/json'
      },
      'body': json.dumps({'errorMessage': 'Internal server error'})
    }
