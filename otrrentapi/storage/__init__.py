""" Initialize azure storage repository """

from config import config

from storage.azurestoragewrapper import StorageTableContext, StorageQueueContext
db = StorageTableContext(**config)
queue = StorageQueueContext(**config)




