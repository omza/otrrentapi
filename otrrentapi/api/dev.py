from flask_restplus import Namespace, Resource, fields
from flask import request, g, session, send_from_directory
from datetime import datetime

from auth import generate_auth_token
from azurestorage import db
from azurestorage.tablemodels import User

db.register_model(User())

# Logger
from config import log, config

api = Namespace('user', description='ottrent api endpoints for user authentification and dev subjects')

@api.route('/postman')
@api.response(404, 'Could not transmit postman collection')
@api.response(200, 'postman collection successfully created.')
class PostmanCollection(Resource):
    
    @api.doc('create postman collection')
    def get(self):
        """ retrieve api as postman collection """

        from flask import json
        from api import api as diboardsapi

        urlvars = False  # Build query strings in URLs
        swagger = True  # Export Swagger specifications
        data = diboardsapi.as_postman(urlvars=urlvars, swagger=swagger)

        return json.dumps(data), 200


""" endpoints for user login """

login = api.model('login with fingerprint and (not required) client',{ 
    'ClientId': fields.String(attribute='PartitionKey', description='Link or path to torrent or video file to be pushed'),
    'Fingerprint': fields.String(attribute='RowKey', required=True, description=''),
    'LoggedIn': fields.Boolean(attribute='loggedin',required=False, description='user identified and logged in', default=False),
    'SessionTimeout': fields.Integer(attribute='timeout', required=False, description='Session Timeout in seconds (default 22)', default=600)
    })


@api.route('/login')
class LoginUser(Resource):

    """ swagger responses """   
    _responses = {}
    _responses['post'] = {200: ('Success', login),
                  400: 'Input payload validation failed',  
                  403: 'Insufficient rights or Bad request (e.g. push credentials not valid)'
                  }

    """ push torrentfile """
    @api.doc(description='login and/or create a new otrrent user and set the session cookie', responses=_responses['post'])
    @api.expect(login)
    @api.marshal_list_with(login)
    def post(self):

        """ parse request data and use model attribute info"""
        data = request.json
        for key, value in login.items():
            if key in data:
                data[value.attribute] = data.pop(key)
                #log.debug('{!s}: {!s}'.format(value.attribute, data[value.attribute]))
        
        """ retrieve user info """
        if 'PartitionKey' in data:
            if data['PartitionKey'] == "":
                data['PartitionKey'] = config['APPLICATION_CLIENT_ID']
        else:
            data['PartitionKey'] = config['APPLICATION_CLIENT_ID']
            
        loginuser = db.get(User(**data))

        """ user exists ? Create a new and  """
        if not db.exists(loginuser):
            loginuser.created = datetime.now()
            db.insert(loginuser)
            
        """ login user """
        #log.debug(loginuser.dict())
        g.user = loginuser
        token = generate_auth_token(loginuser) 
        session['authtoken'] = token

        """ prepare return dict """
        data['loggedin']  = True
        data['timeout'] = 600

        log.debug(session)

        return data, 200 

        