""" Initialize azure storage repository """

from config import config

from storage.azurestoragewrapper import StorageTableContext
db = StorageTableContext(**config)




