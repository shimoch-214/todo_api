import json
import logging
import uuid
import sys
sys.path.append("..")
import errors
from errors import build_response
from models.user_model import UserModel, InvalidPhoneNumberError, InvalidEmailError, InvalidNameError
from pynamodb.exceptions import PutError