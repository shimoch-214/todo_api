import json
import sys

class BadRequest(Exception):
  """
  statusCode 400
  リクエストヘッダ、クエリパラメータ、またはリクエストボディが不正
  """
  pass

class NotFound(Exception):
  """
  statusCode 404
  リクエストされたitemが存在しない
  """
  pass

class UnprocessableEntity(Exception):
  """
  statusCode 409
  create時に該当レコードが存在している
  """
  pass

class InternalError(Exception):
  """
  statusCode 500
  dynamodb接続時のエラー
  """
  pass

class ForbiddenError(Exception):
  """
  statusCode 403
  リソースへの権限なし
  """
  pass

def build_response(e, code):
  return {
    'statusCode': code,
    'headers': {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json'
    },
    'body': json.dumps(
      {
        'statusCode': code,
        'errorMessage': str(e.with_traceback(sys.exc_info()[2]))
      }
    )
  }

