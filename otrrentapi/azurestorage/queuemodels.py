""" imports & Gloabls """
from azurestorage.wrapper import StorageQueueContext, StorageQueueModel 

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


class PushVideoMessage(StorageQueueModel):
    _queuename = 'video'

    epgid = 0
    resolution = ''
    sourcefile = ''
    sourcelink = ''

    protocol = 'ftp'
    server = ''
    port = 21
    user = ''
    password = ''
    destpath = '/'

    otrkeyfile = ''
    videofile = ''
    otruser = ''
    otrpassword = ''
    usecutlist = True
    usesubfolder = False

