""" imports & Gloabls """
import datetime

from azure.common import AzureException, AzureMissingResourceHttpError 
from storage.azurestoragewrapper import StorageQueueContext, StorageQueueModel 
from helpers.helper import safe_cast

""" configure logging """
from config import log


""" Models to determine Queue Message Content ------------------------------------
"""

class PushMessage(StorageQueueModel):
    _queuename = 'push'

    source = ''
    protocol = 'ftp'
    server = ''
    port = 22
    user = ''
    password = ''
    destpath = '/'
    status = 'new'



