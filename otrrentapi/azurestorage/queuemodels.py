""" imports & Gloabls """
import datetime

from azure.common import AzureException, AzureMissingResourceHttpError 
from azurestorage.wrapper import StorageQueueContext, StorageQueueModel 
from helpers.helper import safe_cast

""" configure logging """
from config import log


""" Models to determine Queue Message Content ------------------------------------
"""

class PushMessage(StorageQueueModel):
    _queuename = 'push'

    epgid = 0
    resolution = ''
    sourcefile = ''
    sourcelink = ''

    protocol = 'ftp'
    server = ''
    port = 22
    user = ''
    password = ''
    destpath = '/'


class DownloadMessage(StorageQueueModel):
    _queuename = 'download'

    epgid = 0
    resolution = ''
    sourcefile = ''
    sourcelink = ''
    
    otrkeyfile = ''


class DecodeMessage(StorageQueueModel):
    _queuename = 'decode'

    otrkeyfile = ''
    videofile = ''
    otruser = ''
    otrpassword = ''
    usecutlist = True
    usesubfolder = False

