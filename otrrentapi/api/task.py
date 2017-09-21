from flask_restplus import Namespace, Resource

# Logger
import logging
log = logging.getLogger('diboardapi.' + __name__)

api = Namespace('tools', description='di.boards core tools api endpoints')


@api. route('/resetdb')
@api.response(404, 'Could not create db')
class ResetDatabase(Resource):
    @api.doc('create database')
    def post(self):
        '''create database from scratch'''
        
        from database import db

        try:
            log.warning('try to create db from scratch')
            db.drop_all()
            db.create_all()
            
            return 200

        except:
            api.abort(404, 'Could not create db')


@api. route('/postman')
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

        