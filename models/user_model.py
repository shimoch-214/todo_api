import os
import uuid
from datetime import datetime
import re
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import models.task_model

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
    # validation for phoneNumber
    if not self.phoneNumber:
      raise InvalidPhoneNumberError('The phoneNumber attribute has not to be empty')
    if not isinstance(self.phoneNumber, str):
      raise InvalidPhoneNumberError('The phoneNumber attribute has to be string')
    if not re.match(r'^0\d{9,10}$', self.phoneNumber):
      raise InvalidPhoneNumberError('Invalid phoneNumber')
    # validation for email
    if not self.email:
      raise InvalidEmailError('The email attribute has to be string')
    if not isinstance(self.email, str):
      raise InvalidEmailError('The email attribute has not to be empty')
    if not re.match(r'[A-Za-z0-9\._+]+@[A-Za-z]+\.[A-Za-z]', self.email):
      raise InvalidEmailError('Invalid email')
    if self.email_uniqueness():
      raise InvalidEmailError('This email has been registered')

  def logic_delete(self):
    """
    change deleteFlag to True
    """
    actions = [UserModel.deleteFlag.set(True)]
    self.update(actions)
  
  def email_uniqueness(self):
    check = UserModel.users_gsi_email.query(
      self.email,
      UserModel.deleteFlag == False
    )
    check = [ele for ele in check]
    if len(check) == 0:
      return False
    else:
      if self.id == check[0].id:
        return False
      else:
        return True
  
  def get_tasks(self):
    tasks = models.task_model.TaskModel.scan(
      (models.task_model.TaskModel.userIds.contains(self.id)) &
      (models.task_model.TaskModel.deleteFlag == False)
    )
    return tasks


class InvalidNameError(Exception):
  pass

class InvalidEmailError(Exception):
  pass

class InvalidPhoneNumberError(Exception):
  pass

