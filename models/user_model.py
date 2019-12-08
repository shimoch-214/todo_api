import os
import uuid
from datetime import datetime
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection

class EmailIndex(GlobalSecondaryIndex):
  """
  DynamoDB UserModel
  GSI email: HASH
  """
  class Meta():
    index_name = 'users_gsi_email'
    read_capacity_units = 1
    write_capacity_units = 1
    projection = AllProjection()
  email = UnicodeAttribute(hash_key = True)

class UserModel(Model):
  """
  DYnamoDB UserModel
  """
  class Meta():
    table_name = os.environ['usersTable']
    if os.environ['IS_LOCAL']:
      host = 'http://localhost:8000'
    else:
      host = 'https://dynamodb.{}.amazonaws.com'.format(os.environ['AWS_DEFAULT_REGION'])
  id = UnicodeAttribute(hash_key = True)
  email = UnicodeAttribute()
  users_gsi_email = EmailIndex()
  name = UnicodeAttribute()
  phoneNumber = UnicodeAttribute()
  createdAt = UTCDateTimeAttribute(default = datetime.now())
  updatedAt = UTCDateTimeAttribute(default = datetime.now())
  deleteFlag = BooleanAttribute(default = False)
  
  def __iter__(self):
    for name, attr in self.get_attributes().items():
      if name != 'deleteFlag':
        yield name, attr.serialize(getattr(self, name))

  
  @classmethod
  def get(cls,
          hash_key,
          range_key=None,
          consistent_read=False,
          attributes_to_get=None):
    """
    override: get()
    """
    user = super().get(hash_key, range_key, consistent_read, attributes_to_get)
    if not user.deleteFlag:
      return user
    else:
      raise cls.DoesNotExist()

  def update(self, actions = [], condition = None):
    actions.append(UserModel.updatedAt.set(datetime.now()))
    super().update(actions, condition)

  def logic_delete(self):
    """
    change deleteFlag to True
    """
    actions = [UserModel.deleteFlag.set(True)]
    self.update(actions)
