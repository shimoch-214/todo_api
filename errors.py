import json

class CustomError(Exception):
  """
  必要なattributeが送られなかった場合のエラー
  @extends Exceptionクラスを継承
  """
  def __init__(self, code, message):
    self.code = code
    self.message = message

  def __str__(self):
    response = {
      'statusCode': self.code,
      'headers': {
        'Content-Type': 'application/json',
        'Accept-Charset': 'UTF-8'
      },
      'body': {
        'errorMessage': self.message
      }
    }

    return json.dumps(response)
