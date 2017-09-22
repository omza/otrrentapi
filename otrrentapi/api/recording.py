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
#from azure.storage.table import TableService, Entity

from storage.azurestoragewrapper import StorageTableModel
from storage.tablemodels import Torrent, Recording
from storage import db

db.create_table(Torrent._tablename)
db.create_table(Recording._tablename)

""" init api Namespace """
api = Namespace('tops', description='top recordings including torrentinformation from otr')



""" recordings api models (object serializers)

    recording
    recordingdetail
    
    torrent
    torrentdetail

"""
torrent = api.model('otr torrent tracker entry', {
    'Resolution': fields.String(readOnly=True, description='Recordings resolution'),
    'File': fields.String(attribute='TorrentFile', readOnly=True, description='Recordings resolution'),
    'Source': fields.String(attribute='TorrentLink', readOnly=True, description='Board name'),
    'Finished': fields.Integer(attribute='finished', readOnly=True, description='The identifier of a recording'),
    'Pending': fields.Integer(attribute='loading', readOnly=True, description='The identifier of a recording'),
    'Loaded': fields.Integer(attribute='loaded', readOnly=True, description='The identifier of a recording')})

recording = api.model('top recording public detail',{
    'Id': fields.Integer(readOnly=True, description='The identifier of a recording'),
    'Title': fields.String(attribute='titel', readOnly=True, description='Board name'),
    
    'Start': fields.DateTime(attribute='beginn', readOnly=True, description='Board name'),
    'End': fields.DateTime(attribute='ende', readOnly=True, description='Board name'),
    'Channel': fields.String(attribute='sender', readOnly=True, description='Board description'),

    'Description': fields.String(attribute='text', readOnly=True, description='Board description'),
    'Genre': fields.String(attribute='genre', readOnly=True, description='Board description'),
    'Rating': fields.String(attribute='rating', readOnly=True, description='Board description'),
    'PreviewImage': fields.String(attribute='previewimagelink', readOnly=True, description='Board description')})


recording_detail = api.model('top recording public detail',{
    'Id': fields.Integer(readOnly=True, description='The identifier of a recording'),
    'Title': fields.String(attribute='titel', readOnly=True, description='Board name'),
    
    'Start': fields.DateTime(attribute='beginn', readOnly=True, description='Board name'),
    'End': fields.DateTime(attribute='ende', readOnly=True, description='Board name'),
    'Channel': fields.String(attribute='sender', readOnly=True, description='Board description'),

    'Description': fields.String(attribute='text', readOnly=True, description='Board description'),
    'Genre': fields.String(attribute='genre', readOnly=True, description='Board description'),
    'Rating': fields.String(attribute='rating', readOnly=True, description='Board description'),
    'PreviewImage': fields.String(attribute='previewimagelink', readOnly=True, description='Board description'),
    'Torrents': fields.Nested(attribute='_Torrents',model=torrent, readOnly=True, as_list=True)})


""" Endpoints
    / : Toplist
    /<id:int> : BoardInstance
    /
"""

@api.route('/')
class TopList(Resource):

    """ swagger responses """   
    _responses = {}
    _responses['get'] = {200: ('Success', recording),
                  401: 'Missing Authentification or wrong credentials',
                  403: 'Insufficient rights or Bad request',
                  404: 'No recordings found'
                  }

    """ list/filter boards (public) """
    @api.doc(description='request a list of top recordings with active torrents', security='basicauth', responses=_responses['get'])
    @api.param(name = 'Id', description = 'filter for a single recording with unique board id', type = int)
    @api.param(name = 'Genre', description = 'filter by Genre', type = str)
    @api.param(name = 'Channel', description = 'filter by channel name', type = str)
    @auth.basicauth.login_required
    @api.marshal_list_with(recording)
    def get(self):

        """ list boards with filters """
        # concat filters
        recordfilter = ''
        for key, value in request.args.items():            
            try:
                if key == 'id':
                    recordfilter = recordfilter + 'board.' + key + ' == ' + str(value) + ' AND '
                else:
                    recordfilter = recordfilter + 'board.' + key + ' == \'' + str(value) + '\' AND '
            
            except:
                api.abort(403, __class__._responses['get'][403])
        recordfilter = recordfilter[:-5]       
        
        log.info('retrieve record list with filters {!s}'.format(recordfilter)) 

        """ retrieve Boards with filters """
        toplist = list(db.tableservice.query_entities('recordings', "PartitionKey eq 'top'"))
        if len(toplist) == 0:
            api.abort(404, __class__._responses['get'][404])

        # return httpstatus, object
        return toplist, 200  


@api.route('/<int:id>')
@api.param('id', 'The unique identifier of a top recording')
class TopInstance(Resource):

    # swagger responses   
    _responses = {}
    _responses['get'] = {200: ('Success', recording_detail),
                  401: 'Missing Authentification or wrong credentials',
                  403: 'Insufficient rights or Bad request',
                  404: 'No Recording found'
                  }
    
    """ retrieve toprecording """
    @api.doc(description='show all top recording details to owner and administrator', security='basicauth', responses=_responses['get'])
    @api.marshal_with(recording_detail)
    @auth.basicauth.login_required
    def get(self, id):
        """ request top recording detail data """

        """ logging """
        log.info('select all details for recording: {!s}'.format(id))

        """ retrieve board """
        recording = Recording(db.tableservice, PartitionKey = 'top', RowKey = str(id))
        
        if not recording.exists():
            api.abort(404, __class__._responses['get'][404])

        recording.loadtorrents()

        """ return recording """
        return recording, 200





    