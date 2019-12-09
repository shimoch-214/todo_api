import os
import uuid
from datetime import datetime
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute

class TaskListModel(Model):
  """
  DynamoDB TaskListModel
  """
  class Meta():
    table_name = os.environ['taskListsTable']
    if 'IS_LOCAL' in os.environ:
      host = 'http://localhost:8000'
    else:
      region = os.environ['AWS_REGION']
      host = 'https://dynamodb.{}.amazonaws.com'.format(region)
  id = UnicodeAttribute(hash_key = True)
  name = UnicodeAttribute()
  description = UnicodeAttribute()
  createdAt = UTCDateTimeAttribute(default = datetime.now())
  updatedAt = UTCDateTimeAttribute()
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
    task_list = super().get(hash_key, range_key, consistent_read, attributes_to_get)
    if not task_list.deleteFlag:
      return task_list
    else:
      raise cls.DoesNotExist()
    
  def update(self, actions = [], condition = None):
    actions.append(TaskListModel.updatedAt.set(datetime.now()))
    super().update(actions, condition)
  
  def save(self, condition = None):
    self.before_save()
    self.updatedAt = datetime.now()
    super().save(condition)

  def before_save(self):
    # validation for name
    if not self.name:
      raise InvalidNameError('The name attribute has not to be empty')
    if not isinstance(self.name, str):
      raise InvalidNameError('The name attribute has to be string')
    # validation for description
    if not self.description:
      raise InvalidDescriptionError('The description attribute has not to be empty')
    if not isinstance(self.description, str):
      raise InvalidDescriptionError('The description attribute has to be string')

  def logic_delete(self):
    """
    change deleteFlag to True
    """
    actions = [TaskListModel.deleteFlag.set(True)]
    self.update(actions)

class InvalidNameError(Exception):
  pass

class InvalidDescriptionError(Exception):
  pass



