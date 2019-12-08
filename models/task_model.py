import os
import uuid
from datetime import datetime
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute, UnicodeSetAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection

class TaskListIdIndex(GlobalSecondaryIndex):
  """
  DynamoDB TaskModel
  GSI TaskListId: HASH
  """
  class Meta():
    index_name = 'tasks_gsi_taskListId'
    read_capacity_units = 1
    write_capacity_units = 1
    projection = AllProjection()
  taskListId = UnicodeAttribute(hash_key = True)

class TaskModel(Model):
  """
  DynamoDB TaskModel
  """
  class Meta():
    table_name = os.environ['tasksTable']
    if os.environ['IS_LOCAL']:
      host = 'http://localhost:8000'
    else:
      host = 'https://dynamodb.{}.amazonaws.com'.format(os.environ['AWS_DEFAULT_REGION'])
  id = UnicodeAttribute(hash_key = True)
  name = UnicodeAttribute()
  description = UnicodeAttribute()
  taskListId = UnicodeAttribute()
  tasks_gsi_taskListId = TaskListIdIndex()
  userIds = UnicodeSetAttribute()
  done = BooleanAttribute(default = False)
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
    task = super().get(hash_key, range_key, consistent_read, attributes_to_get)
    if not task.deleteFlag:
      return task
    else:
      raise cls.DoesNotExist()

  def update(self, actions = [], condition = None):
    actions.append(TaskModel.updatedAt.set(datetime.now()))
    super().update(actions, condition)
  
  def save(self, condition = None):
    self.updatedAt = datetime.now()
    super().save(condition)

  def logic_delete(self):
    """
    change deleteFlag to True
    """
    actions = [TaskModel.deleteFlag.set(True)]
    self.update(actions)