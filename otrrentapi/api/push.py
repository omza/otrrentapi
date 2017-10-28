""" imports & globals """

from flask import request, g, send_from_directory
from flask_restplus import Namespace, Resource, fields
import os
from datetime import datetime, timedelta
import auth
from helpers.helper import test_ftpconnection

""" configuration """
from config import config, log

""" import & Init storage """
#from storage.azurestoragewrapper import StorageTableModel
from azurestorage.queuemodels import PushMessage, DecodeMessage, DownloadMessage, PushVideoMessage
from azurestorage import queue

queue.register_model(PushMessage())
queue.register_model(DecodeMessage())
queue.register_model(DownloadMessage())
queue.register_model(PushVideoMessage())

""" init api Namespace """
api = Namespace('push', description='endpoints to initiate ftp push')


""" recordings api models (object serializers)
    push
    decode
"""

job = api.model('job data',{ 
    'Task-Id': fields.String(attribute='id', ReadOnly=True, description='Link or path to torrent or video file to be pushed'),
    'Created': fields.DateTime(attribute='insertion_time', ReadOnly=True, required=False, description='Timestamp job created')
    })

source = api.model('top recording source file data',{
    'Epg-Id': fields.Integer(attribute='epgid', required=False, description='epg_id to video metadata from otr epg',default=0),
    'Resolution': fields.String(attribute='resolution', required=False, description='Resolution of video file (e.g. HD, HQ)', default=''),
    'File': fields.String(attribute='sourcefile', required=True, description='torrent or video file to be pushed'),
    'Link': fields.String(attribute='sourcelink', required=True, description='Link or path to torrent or video file to be pushed')
    })

destination = api.model('top recording ftp destination data',{      
    'Protocol': fields.String(attribute='protocol', required=False , description='Determine push protocol ftp or sftp (default ftp)', default='ftp'),
    'Server': fields.String(attribute='server', required=True, description='push destination server'),
    'Port': fields.Integer(attribute='port', required=False, description='Port on push destination server (default 22)', default=21),
    'User': fields.String(attribute='user', required=True, description='credentials for push destination server'),
    'Password': fields.String(attribute='password', required=True, description='credentials for push destination server'),
    'ServerPath': fields.String(attribute='destpath', required=False, description='push to path on destination server (default = /)', default='/')
    })

decoding = api.model('top recording decode video data',{
    'OtrkeyFile': fields.String(attribute='otrkeyfile', required=False, description='otrkey file to be decoded', default=''),
    'VideoFile': fields.String(attribute='videofile', required=False, description='videofile file to be pushed', default=''),
    'Otr-User': fields.String(attribute='otruser', required=True, description='credentials for otr server'),
    'Otr-Password': fields.String(attribute='otrpassword', required=True, description='credentials for otr server'),
    'UseCutlist': fields.Boolean(attribute='usecutlist', required=False, description='Use auto-cutlist during decoding otrkey file(default True)', default=True),
    'UseSubfolder': fields.Boolean(attribute='usesubfolder',required=False, description='Use auto-cutlist during decoding otrkey file(default False)', default=False)
    })

push_detail = api.model('top recording push torrent data incl. Job',{})
push_detail.update(job)
push_detail.update(source)
push_detail.update(destination)

push = api.model('top recording push torrent data',{})
push.update(source)
push.update(destination)

video_detail = api.model('jobchain to download, decode and push a otr recording video file',{})
video_detail.update(job)
video_detail.update(source)
video_detail.update(decoding)
video_detail.update(destination)

video = api.model('top recording push video job data',{})
video.update(source)
tmp = decoding
tmp.pop('OtrkeyFile')
tmp.pop('VideoFile')
video.update(tmp)
video.update(destination)



""" Endpoints
    / : Toplist
    /<id:int> : BoardInstance
    /
"""
 
@api.route('/torrent')
class Push(Resource):

    """ swagger responses """   
    _responses = {}
    _responses['post'] = {200: ('Success', push_detail),
                  400: 'Input payload validation failed',  
                  401: 'Missing Authentification or wrong credentials',
                  403: 'Insufficient rights or Bad request (e.g. push credentials not valid)'
                  }

    """ push torrentfile """
    @api.doc(description='create a new push task for torrentfiles in queue to be worked off', security='basicauth', responses=_responses['post'])
    @auth.basicauth.login_required
    @api.expect(push)
    @api.marshal_list_with(push_detail)
    def post(self):
        """ create push job in queue for torrent/video file """

        """ parse request data and use model attribute info"""
        data = request.json
        log.debug(data)
        
        for key, value in push.items():
            if key in data:
                data[value.attribute] = data.pop(key)

        """ further validations:
            test connection to ftp destination server
        """
        validftp, validftpmessage = test_ftpconnection(data['server'], data['port'], data['user'], data['password'], data['destpath'])
        if not validftp:
            log.error(validftpmessage)
            api.abort(403, __class__._responses['post'][403] + ': ' + validftpmessage)
        
        """ init a PushMessage instance and put it into queue """
        message = PushMessage(**data)
        message = queue.put(message)
        if message is None:
            api.abort(403, __class__._responses['post'][403])

        """ return message """
        message.password = '<encrypted>'
        log.debug('mesage input: {!s}, {!s}, {!s}'.format(message.getmessage(), message.id, message.insertion_time))
        return message, 200 

@api.route('/video')
class Decode(Resource):

    """ swagger responses """   
    _responses = {}
    _responses['post'] = {200: ('Success', video_detail),
                  400: 'Input payload validation failed',
                  401: 'Missing Authentification or wrong credentials',
                  403: 'Insufficient rights or Bad request'
                  }

    """ dowload, decode and push video file """
    @api.doc(description='create a new push task for a decoded video in queue to be worked off', security='basicauth', responses=_responses['post'])
    @auth.basicauth.login_required
    @api.expect(video)
    @api.marshal_list_with(video_detail)
    def post(self):

        """ create a new push task for a decoded video in queue to be worked off (only available for PRO clients) """

        """ retrieve client role """
        AuthUser = g.get('clientrole')
        if AuthUser is None:
             api.abort(401, __class__._responses['post'][401])

        if AuthUser != 'PRO':
            api.abort(403, __class__._responses['post'][403])

        """ parse request data and use model attribute info"""
        requestbody = request.json
        log.debug(requestbody)

        """ further validations:
            test connection to ftp destination server
        """
        validftp, validftpmessage = test_ftpconnection(requestbody['Server'], requestbody['Port'], requestbody['User'], requestbody['Password'], requestbody['ServerPath'])
        if not validftp:
            log.error(validftpmessage)
            api.abort(403, __class__._responses['post'][403] + ': ' + validftpmessage)
           

        """ create jobchain DownloadMessage -----------------------------------------------------------------"""
        Content = {}
        for key, value in requestbody.items():
            if key in video.keys():
                Content[video[key].attribute]=value

        message = PushVideoMessage(**Content)
        
        """ update otrkey filename as output """
        message.otrkeyfile = os.path.splitext(os.path.basename(message.sourcelink))[0]
        message.videofile = os.path.splitext(os.path.basename(message.otrkeyfile))[0]
        
        """ put download queue message """
        message = queue.put(message)
        if message is None:
            api.abort(403, __class__._responses['post'][403])

        """ prepare return data """
        message.otrpassword = '<encrypted>'
        message.password = '<encrypted>'

        return message, 200 
