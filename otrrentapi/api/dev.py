from flask_restplus import Namespace, Resource

# Logger
from config import log

api = Namespace('dev', description='ottrent api endpoints for developers')

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

        