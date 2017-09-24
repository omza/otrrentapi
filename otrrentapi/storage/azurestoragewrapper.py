""" imports & globals """
from azure.common import AzureMissingResourceHttpError, AzureException
from azure.storage.table import TableService, Entity
from azure.storage.queue import QueueService
from helpers.helper import safe_cast

import datetime

""" configure logging """
from config import log


class StorageTableContext():
    """Initializes the repository with the specified settings dict.
        Required settings in config dict are:
        - AZURE_STORAGE_NAME
        - STORAGE_KEY
    """
    
    _models = []
    _tableservice = None
    _storage_key = ''
    _storage_name = ''

    def __init__(self, **kwargs):

        self._storage_name = kwargs.get('AZURE_STORAGE_NAME', '')
        self._storage_key = kwargs.get('AZURE_STORAGE_KEY', '')

        """ service init """
        self._models = []
        if self._storage_key != '' and self._storage_name != '':
            self._tableservice = TableService(self._storage_name, self._storage_key)

        pass
     
    def __createtable__(self, tablename) -> bool:
        if (not self._tableservice is None):
            try:
                self._tableservice.create_table(tablename)
                return True
            except AzureException as e:
                log.error('failed to create {} with error {}'.format(tablename, e))
                return False
        else:
            return True
        pass

    def register_model(self, storagemodel):
        if isinstance(storagemodel, StorageTableModel):
            modelname = storagemodel.__class__.__name__
            if (not modelname in self._models):
                self.__createtable__(storagemodel._tablename)
                self._models.append(modelname)
        pass

    def table_isempty(self, tablename, PartitionKey='', RowKey = '') -> bool:
        if  (not self.tableservice is None):

            filter = "PartitionKey eq '{}'".format(PartitionKey) if PartitionKey != '' else ''
            if filter == '':
                filter = "RowKey eq '{}'".format(RowKey) if RowKey != '' else ''
            else:
                filter = filter + ("and RowKey eq '{}'".format(RowKey) if RowKey != '' else '')
            try:
                entities = list(self._tableservice.query_entities(tablename, filter = filter, select='PartitionKey', num_results=1))
                if len(entities) == 1: 
                    return False
                else:
                    return True

            except AzureMissingResourceHttpError as e:
                log.debug('failed to query {} with error {}'.format(tablename, e))
                return True

        else:
            return True
        pass

    def exists(self, storagemodel) -> bool:
        exists = False
        if isinstance(storagemodel, StorageTableModel):
            modelname = storagemodel.__class__.__name__
            if (modelname in self._models):
                if storagemodel._exists is None:
                    try:
                        entity = self._tableservice.get_entity(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey)
                        storagemodel._exists = True
                        exists = True
            
                    except AzureMissingResourceHttpError:
                        storagemodel._exists = False
                else:
                    exists = storagemodel._exists
            else:
                log.debug('please register model {} first'.format(modelname))
                        
        return exists       

    def get(self, storagemodel) -> StorageTableModel:
        """ load entity data from storage to vars in self """

        if isinstance(storagemodel, StorageTableModel):
            modelname = storagemodel.__class__.__name__
            if (modelname in self._models):

                try:
                    entity = self._tableservice.get_entity(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey)
                    storagemodel._exists = True
        
                    """ sync with entity values """
                    for key, default in vars(storagemodel).items():
                        if not key.startswith('_') and key not in ['','PartitionKey','RowKey']:
                            value = getattr(entity, key, None)
                            if not value is None:
                                setattr(storagemodel, key, value)
             
                except AzureMissingResourceHttpError as e:
                    log.debug('can not get table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(self._tablename, self._PartitionKey, self._RowKey, e))
                    storagemodel._exists = False

            else:
                log.debug('please register model {} first'.format(modelname))

            return storagemodel

        else:
            return None

    def insert(self, storagemodel) -> StorageTableModel:
        """ insert model into storage """
        try:            
            self._tableservice.insert_or_replace_entity(storagemodel._tablename, storagemodel.dict())
            storagemodel._exists = True

        except AzureMissingResourceHttpError as e:
            log.debug('can not insert or replace table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey, e))

        return storagemodel

    def merge(self, storagemodel) -> StorageTableModel:
        """ try to merge entry """
        try:            
            self._tableservice.insert_or_merge_entity(self._tablename, storagemodel.dict())
                
            """ sync storagemodel """
            storagemodel = self.get(storagemodel)

        except AzureMissingResourceHttpError as e:
            log.error('can not insert or merge table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey, e))

        return storagemodel
    
    def delete(self):
        """ delete existing Entity """
        try:
            self._tableservice.delete_entity(self._tablename, self._PartitionKey, self._RowKey)
            self._existsinstorage = False

        except AzureMissingResourceHttpError as e:
            log.debug('can not delete table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(self._tablename, self._PartitionKey, self._RowKey, e))

    def __changeprimarykeys__(self, PartitionKey = '', RowKey = ''):
        """ Change Entity Primary Keys into new instance:

            - PartitionKey and/or
            - RowKey
        """

        PartitionKey = PartitionKey if PartitionKey != '' else self._PartitionKey
        RowKey = RowKey if RowKey != '' else self._RowKey

        """ change Primary Keys if different to existing ones """
        if (PartitionKey != self._PartitionKey) or (RowKey != self._RowKey):
            return True, PartitionKey, RowKey
        else:
            return False, PartitionKey, RowKey
        pass
            
    def moveto(self, PartitionKey = '', RowKey = ''):
        """ Change Entity Primary Keys and move in Storage:

            - PartitionKey and/or
            - RowKey
        """
        changed, PartitionKey, RowKey = self.__changeprimarykeys__(PartitionKey, RowKey)

        if changed:

            """ sync self """
            new = self.copyto(PartitionKey, RowKey)
            new.save()

            """ delete Entity if exists in Storage """
            self.delete()

    def copyto(self, PartitionKey = '', RowKey = '') -> object:
        """ Change Entity Primary Keys and copy to new Instance:

            - PartitionKey and/or
            - RowKey
        """
        changed, PartitionKey, RowKey = self.__changeprimarykeys__(PartitionKey, RowKey)

        self.load()
        new = self
        new._PartitionKey = PartitionKey
        new._RowKey = RowKey
        new.load()

        return new

class StorageTableModel(object):
    _tablename = ''
    _dateformat = ''
    _datetimeformat = ''
    _exists = None

    def __init__(self, **kwargs):                  
        """ constructor """
        
        self._tablename = self.__class__._tablename
        self._dateformat = self.__class__._dateformat
        self._datetimeformat = self.__class__._datetimeformat
        self._exists = None
               
        """ parse **kwargs into instance var """
        self.PartitionKey = kwargs.get('PartitionKey', '')
        self.RowKey = kwargs.get('RowKey', '')

        for key, default in vars(self.__class__).items():
            if not key.startswith('_') and key != '':
                if key in kwargs:
                   
                    value = kwargs.get(key)
                    to_type = type(default)
                
                    if to_type is StorageTableCollection:
                        setattr(self, key, value)

                    elif to_type is datetime.datetime:
                        setattr(self, key, safe_cast(value, to_type, default, self._datetimeformat))

                    elif to_type is datetime.date:
                        setattr(self, key, safe_cast(value, to_type, default, self._dateformat))

                    else:
                        setattr(self, key, safe_cast(value, to_type, default))
                
                else:
                    setattr(self, key, default)

        """ set primary keys from data"""
        if self._PartitionKey == '':
            self.__setPartitionKey__()

        if self._RowKey == '':
            self.__setRowKey__()
         
    def __setPartitionKey__(self):
        """ parse storage primaries from instance attribute 
            overwrite if inherit this class
        """
        pass

    def __setRowKey__(self):
        """ parse storage primaries from instance attribute 
            overwrite if inherit this class
        """
        pass

    def dict(self) -> dict:        
        """ parse self into dictionary """
     
        image = {}

        for key, value in vars(self).items():
            if not key.startswith('_') and key !='':                  
                    
                if isinstance(value, StorageTableCollection):
                    image[key] = getattr(self, key).list()

                else:
                    image[key] = value                    
        
        return image

class StorageTableCollection():
    _tablename = ''
    _filter = ''
    _entities = []
    _count = -1

    def __init__(self, tablename='', filter='*'):
        """ constructor """

        """ query configuration """
        self._tablename = tablename if tablename != '' else self.__class__._tablename
        self._filter = filter        
        self._entities = []
        self._count = -1
        pass

            
    def list(self) -> list:
        return list(self._entities)

    def count(self) -> int:
        return self._count

    def find(self, key, value):
        pass

    pass
