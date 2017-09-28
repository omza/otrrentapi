""" imports & globals """
from azure.common import AzureMissingResourceHttpError, AzureException
from azure.storage.table import TableService, Entity
from azure.storage.queue import QueueService, QueueMessage
from helpers.helper import safe_cast


import datetime
from ast import literal_eval

""" configure logging """
from config import log

""" encryption """
from azurestorage.encryption import (
    KeyWrapper,
    KeyResolver    
    )

""" model base classes """
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
        if self.PartitionKey == '':
            self.__setPartitionKey__()

        if self.RowKey == '':
            self.__setRowKey__()

        """ initialize collectionobjects """
        self.__setCollections__()
        pass

         
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

    def __setCollections__(self):
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

class StorageTableCollection(list):
    _tablename = ''
    _filter = ''

    def __init__(self, tablename='', filter='*'):
        """ constructor """

        """ query configuration """
        self._tablename = tablename if tablename != '' else self.__class__._tablename
        self._filter = filter        
        pass

    def find(self, key, value) -> dict:
        pass

    def filter(self, key, values):

        resultset = [item for item in self if item[key] in values]
        self.clear()
        self.extend(resultset)

    pass

class StorageQueueModel(QueueMessage):
    _queuename = ''
    _dateformat = ''
    _datetimeformat = ''
    
    def __init__(self, **kwargs):                  
        """ constructor """
        super().__init__()
        self._queuename = self.__class__._queuename
        self._dateformat = self.__class__._dateformat
        self._datetimeformat = self.__class__._datetimeformat
               
        """ parse **kwargs in tmp dict var """
        for key, default in vars(self.__class__).items():
            if not key.startswith('_') and key != '':
                if (not key in vars(QueueMessage).items()):
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

    def getmessage(self) -> str:
        """ parse self into unicode string as message content """   
        image = {}
        for key, default in vars(self.__class__).items():
            if not key.startswith('_') and key !='':                                      
                image[key] = getattr(self, key, default)                                  
        return str(image)

    def mergemessage(self, message):
        """ parse OueueMessage in Model vars """
        if isinstance(message, QueueMessage):
            """ merge queue message vars """
            for key, value in vars(message).items():
                setattr(self, key, value)

            """ parse message content """
            try:
                content = literal_eval(message.content)
                for key, value in content.items():
                    setattr(self, key, value)

            except:
                log.exception('cant parse message {} into attributes.'.format(message.content))
        pass


""" wrapper classes """

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
            self._tableservice = TableService(account_name = self._storage_name, account_key = self._storage_key, protocol='https')

     
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

    def register_model(self, storagemodel:object):
        modelname = storagemodel.__class__.__name__     
        if isinstance(storagemodel, StorageTableModel):
            if (not modelname in self._models):
                self.__createtable__(storagemodel._tablename)
                self._models.append(modelname)
                log.info('model {} registered successfully. Models are {!s}'.format(modelname, self._models))      
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
                    log.debug('can not get table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey, e))
                    storagemodel._exists = False

            else:
                log.debug('please register model {} first to {!s}'.format(modelname, self._models))

            return storagemodel

        else:
            return None

    def insert(self, storagemodel) -> StorageTableModel:
        """ insert model into storage """
        if isinstance(storagemodel, StorageTableModel):
            modelname = storagemodel.__class__.__name__
            if (modelname in self._models):
                try:            
                    self._tableservice.insert_or_replace_entity(storagemodel._tablename, storagemodel.dict())
                    storagemodel._exists = True

                except AzureMissingResourceHttpError as e:
                    log.debug('can not insert or replace table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey, e))
            else:
                log.debug('please register model {} first'.format(modelname))

            return storagemodel
        else:
            return None

    def merge(self, storagemodel) -> StorageTableModel:
        """ try to merge entry """
        if isinstance(storagemodel, StorageTableModel):
            modelname = storagemodel.__class__.__name__
            if (modelname in self._models):
                try:            
                    self._tableservice.insert_or_merge_entity(storagemodel._tablename, storagemodel.dict())
                    storagemodel._exists = True

                except AzureMissingResourceHttpError as e:
                    log.debug('can not insert or merge table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey, e))
            else:
                log.debug('please register model {} first'.format(modelname))

            return storagemodel
        else:
            return None
    
    def delete(self,storagemodel):
        """ delete existing Entity """
        if isinstance(storagemodel, StorageTableModel):
            modelname = storagemodel.__class__.__name__
            if (modelname in self._models):
                try:
                    self._tableservice.delete_entity(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey)
                    storagemodel._exists = False

                except AzureMissingResourceHttpError as e:
                    log.debug('can not delete table entity:  Table {}, PartitionKey {}, RowKey {} because {!s}'.format(storagemodel._tablename, storagemodel.PartitionKey, storagemodel.RowKey, e))

            else:
                log.debug('please register model {} first'.format(modelname))

            return storagemodel
        else:
            return None


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

    def query(self, storagecollection) -> StorageTableCollection:
        if isinstance(storagecollection, StorageTableCollection):
            try:
                storagecollection.extend(self._tableservice.query_entities(storagecollection._tablename,storagecollection._filter))

            except AzureMissingResourceHttpError as e:
                log.debug('can not query table {} with filters {} because {!s}'.format(storagecollection._tablename, storagecollection._filter, e))            

            return storagecollection
        else:
            return None

class StorageQueueContext():
    """Initializes the repository with the specified settings dict.
        Required settings in config dict are:
        - AZURE_STORAGE_NAME
        - AZURE_STORAGE_KEY
    """
    
    _models = []
    _service = None
    _storage_key = ''
    _storage_name = ''

    def __init__(self, **kwargs):

        self._storage_name = kwargs.get('AZURE_STORAGE_NAME', '')
        self._storage_key = kwargs.get('AZURE_STORAGE_KEY', '')

        """ service init """
        if self._storage_key != '' and self._storage_name != '':
            self._service = QueueService(account_name = self._storage_name, account_key = self._storage_key, protocol='https')

        """ registered models """
        self._models = []

        """ encrypt queue service """
        if kwargs.get('AZURE_REQUIRE_ENCRYPTION', False):

            # Create the KEK used for encryption.
            # KeyWrapper is the provided sample implementation, but the user may use their own object as long as it implements the interface above.
            kek = KeyWrapper(kwargs.get('AZURE_KEY_IDENTIFIER', 'otrrentapi'), kwargs.get('SECRET_KEY', 'super-duper-secret')) # Key identifier

            # Create the key resolver used for decryption.
            # KeyResolver is the provided sample implementation, but the user may use whatever implementation they choose so long as the function set on the service object behaves appropriately.
            key_resolver = KeyResolver()
            key_resolver.put_key(kek)

            # Set the require Encryption, KEK and key resolver on the service object.
            self._service.require_encryption = True
            self._service.key_encryption_key = kek
            self._service.key_resolver_funcion = key_resolver.resolve_key
        pass
     
    def __create__(self, queue) -> bool:
        if (not self._service is None):
            try:
                self._service.create_queue(queue)
                return True
            except AzureException as e:
                log.error('failed to create {} with error {}'.format(queue, e))
                return False
        else:
            return True
        pass

    def register_model(self, storagemodel:object):
        modelname = storagemodel.__class__.__name__     
        if isinstance(storagemodel, StorageQueueModel):
            if (not modelname in self._models):
                self.__create__(storagemodel._queuename)
                self._models.append(modelname)
                log.info('model {} registered successfully. Models are {!s}'.format(modelname, self._models))      
        pass

    def put(self, storagemodel:object) -> StorageQueueModel:
        """ insert queue message into storage """

        modelname = storagemodel.__class__.__name__
        if isinstance(storagemodel, StorageQueueModel):
            if (modelname in self._models):
                """ peek first message in queue """
                try:
                    message = self._service.put_message(storagemodel._queuename, storagemodel.getmessage())
                    storagemodel.mergemessage(message)

                except AzureException as e:
                    log.debug('can not save queue message:  queue {} with message {} because {!s}'.format(storagemodel._queuename, storagemodel.content, e))                    
            else:
                log.debug('please register model {} first'.format(modelname))
        else:
            log.debug('model {} is not a Queue Model'.format(modelname))

        return storagemodel

    def peek(self, storagemodel:object) -> StorageQueueModel:
        """ lookup the next message in queue """

        modelname = storagemodel.__class__.__name__
        if isinstance(storagemodel, StorageQueueModel):
            if (modelname in self._models):
                """ peek first message in queue """
                try:
                    messages = self._service.peek_messages(storagemodel._queuename, num_messages=1)

                    """ parse retrieved message """
                    for message in messages:
                        storagemodel.mergemessage(message)

                    """ no message retrieved ?"""
                    if storagemodel.id is None:
                        storagemodel = None

                except AzureException as e:
                    log.debug('can not peek queue message:  queue {} with message {} because {!s}'.format(storagemodel._queuename, storagemodel.content, e))                     
            else:
                log.debug('please register model {} first'.format(modelname))
        else:
            log.debug('model {} is not a Queue Model'.format(modelname))

        return storagemodel

    def get(self, storagemodel:object, hide = 0) -> StorageQueueModel:
        """ lookup the next message in queue """
        modelname = storagemodel.__class__.__name__
        if isinstance(storagemodel, StorageQueueModel):
            if (modelname in self._models):
                """ get first message in queue """
                try:
                    if hide > 0:
                        messages = self._service.get_messages(storagemodel._queuename, num_messages=1, visibility_timeout = hide)
                    else:
                        messages = self._service.get_messages(storagemodel._queuename, num_messages=1)
                    
                    """ parse retrieved message """
                    for message in messages:
                        storagemodel.mergemessage(message)

                    """ no message retrieved ?"""
                    if storagemodel.id is None:
                        storagemodel = None

                except AzureException as e:
                    log.debug('can not get queue message:  queue {} with message {} because {!s}'.format(storagemodel._queuename, storagemodel.content, e))                     
            else:
                log.debug('please register model {} first'.format(modelname))
        else:
            log.debug('model {} is not a Queue Model'.format(modelname))

        return storagemodel

    def update(self, storagemodel:object, hide = 0) -> StorageQueueModel:
        """ update the message in queue """
        modelname = storagemodel.__class__.__name__
        if isinstance(storagemodel, StorageQueueModel):
            if (modelname in self._models):
                """ check if message in queue """
                if (storagemodel.id != '') and (storagemodel.pop_receipt != '') and (not storagemodel.id is None) and (not storagemodel.pop_receipt is None):
                    try:
                        content = storagemodel.getmessage()
                        message = self._service.update_message(storagemodel._queuename, storagemodel.id, storagemodel.pop_receipt, visibility_timeout = hide, content=content)
                        storagemodel.content = content
                        storagemodel.pop_receipt = message.pop_receipt

                    except AzureException as e:
                        log.debug('can not update queue message:  queue {} with message.id {!s} because {!s}'.format(storagemodel._queuename, storagemodel.id, e))
                else:
                    log.debug('cant update queuemessage {} due to missing id and pop_receipt'.format(modelname))                
            else:
                log.debug('please register model {} first'.format(modelname))
        else:
            log.debug('model {} is not a Queue Model'.format(modelname))

        return storagemodel

    def delete(self, storagemodel:object) -> bool:
        """ delete the message in queue """
        modelname = storagemodel.__class__.__name__
        deleted = False
        if isinstance(storagemodel, StorageQueueModel):
            if (modelname in self._models):
                """ check if message in queue """
                if (storagemodel.id != '') and (storagemodel.pop_receipt != '') and (not storagemodel.id is None) and (not storagemodel.pop_receipt is None):
                    try:
                        self._service.delete_message(storagemodel._queuename, storagemodel.id, storagemodel.pop_receipt)
                        deleted = True

                    except AzureException as e:
                        log.debug('can not delete queue message:  queue {} with message.id {!s} because {!s}'.format(storagemodel._queuename, storagemodel.id, e))
                else:
                    log.debug('cant update queuemessage {} due to missing id and pop_receipt'.format(modelname))                
            else:
                log.debug('please register model {} first'.format(modelname))
        else:
            log.debug('model {} is not a Queue Model'.format(modelname))

        return deleted
