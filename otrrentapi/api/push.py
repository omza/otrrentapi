""" imports & globals """

from flask import request, g, send_from_directory
from flask_restplus import Namespace, Resource, fields
import os
from datetime import datetime, timedelta
import auth

""" configuration """
from config import config, log
log.name = log.name +'.'+__name__

""" import & Init storage """
#from storage.azurestoragewrapper import StorageTableModel
from storage.queuemodels import PushMessage
from storage import queue

queue.register_model(PushMessage())

""" init api Namespace """
api = Namespace('push', description='endpoints to initiate ftp push')



""" recordings api models (object serializers)

    push
    decode
    download


"""

push = api.model('top recording public detail',{   
    'Source': fields.String(attribute='source', required=True, description='Link or path to torrent or video file to be pushed'),
    
    'Protocol': fields.String(attribute='protocol', required=False , description='Determine push protocol ftp or sftp (default ftp)'),
    'Server': fields.String(attribute='server', required=True, description='push destination server'),
    'Port': fields.Integer(attribute='port', required=False, description='Port on push destination server (default 22)'),
    'User': fields.String(attribute='user', required=True, description='credentials for push destination server'),
    'Password': fields.String(attribute='password', required=True, description='credentials for push destination server'),

    'Path': fields.String(attribute='destpath', required=False, description='push to path on destination server (default = /)')})


""" Endpoints
    / : Toplist
    /<id:int> : BoardInstance
    /
"""
 
@api.route('/')
class Push(Resource):

    """ swagger responses """   
    _responses = {}
    _responses['post'] = {200: ('Success', push),
                  401: 'Missing Authentification or wrong credentials',
                  403: 'Insufficient rights or Bad request',
                  404: 'No recordings found'
                  }

    """ list/filter boards (public) """
    @api.doc(description='create a new push task in queue to be worked off', security='basicauth', responses=_responses['post'])
    @auth.basicauth.login_required
    @api.expect(push)
    @api.marshal_list_with(push)
    def post(self):

        return [], 200 

@api.route('/<int:id>')
@api.param('id', 'The unique identifier of a otrrent task')
class PushInstance(Resource):

    # swagger responses   
    _responses = {}
    _responses['get'] = {200: ('Success', push),
                  401: 'Missing Authentification or wrong credentials',
                  403: 'Insufficient rights or Bad request',
                  404: 'No Recording found'
                  }
    _responses['put'] = _responses['get']
    _responses['delete'] = _responses['get']

    """ retrieve task status """
    @api.doc(description='get Taskstatus from queue', security='basicauth', responses=_responses['get'])
    @api.marshal_with(push)
    @auth.basicauth.login_required
    def get(self, id):
        """ request task detail data """

        """ return task """
        return [], 200

    """ update task  """
    @api.doc(description='change Task in queue', security='basicauth', responses=_responses['put'])
    @api.marshal_with(push)
    @auth.basicauth.login_required
    def put(self, id):
        """ request task detail data """

        """ return task """
        return [], 200

    """ delete task  """
    @api.doc(description='change Task in queue', security='basicauth', responses=_responses['delete'])
    @api.marshal_with(push)
    @auth.basicauth.login_required
    def delete(self, id):
        """ request task detail data """

        """ return task """
        return [], 200
