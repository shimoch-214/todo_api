import json

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

