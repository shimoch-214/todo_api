import os
import uuid
from datetime import datetime
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute, UnicodeSetAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import models.user_model
import models.task_list_model

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
    # validation for taskListId
    if not self.taskListId:
      raise InvalidTaskListError('The taskListId attribute has not to be empty')
    if not isinstance(self.taskListId, str):
      raise InvalidTaskListError('The taskListId attribute has to be string')
    try:
      self.get_task_list()
    except models.task_list_model.TaskListModel.DoesNotExist:
      raise InvalidTaskListError('The taskList does not exist')
    # validation for userIds
    if not (isinstance(self.userIds, list) or isinstance(self.userIds, set)):
      raise InvalidUserError('The userIds attribute has to be array')
    else:
      for user_id in self.userIds:
        if not isinstance(user_id, str):
          raise InvalidUserError('The userIds contains only strings')
    try:
      self.get_users()
    except models.user_model.UserModel.DoesNotExist:
      raise InvalidUserError('The userIds contains a invalid userId')

  def get_task_list(self):
    task_list = models.task_list_model.TaskListModel.get(self.taskListId)
    return task_list

  def get_users(self):
    users = []
    for user_id in self.userIds:
      user = models.user_model.UserModel.get(user_id)
      users.append(user)
    return users

  def logic_delete(self):
    """
    change deleteFlag to True
    """
    actions = [TaskModel.deleteFlag.set(True)]
    self.update(actions)

  def status_update(self, flag):
    """
    change done_flag
    """
    actions = [TaskModel.done.set(flag)]
    self.update(actions)
  
  def user_ids_update(self, user_ids, flag):
    user_ids = set(user_ids)
    for user_id in user_ids:
      try:
        models.user_model.UserModel.get(user_id)
      except models.user_model.UserModel.DoesNotExist:
        raise InvalidUserError('The userIds contains a invalid userId')
    if flag:
      actions = [TaskModel.userIds.add(user_ids)]
    else:
      actions = [TaskModel.userIds.delete(user_ids)]
    self.update(actions)

class InvalidNameError(Exception):
  pass

class InvalidDescriptionError(Exception):
  pass

class InvalidTaskListError(Exception):
  pass

class InvalidUserError(Exception):
  pass