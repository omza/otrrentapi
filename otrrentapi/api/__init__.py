""" imports & globals -------------------------------------------------------------
"""
import os

from flask import Blueprint, json
from flask_restplus import Api

from api.recording import api as recording_ns
from api.push import api as push_ns
from api.dev import api as dev_ns

from auth import authorizations

""" configuration  & logging"""
from config import config, log


""" register flask_restplus api and namespaces as blueprint ------------------
"""

otrrentapi = Blueprint('api', __name__, url_prefix='/api')

api = Api(otrrentapi,
    title='otrrent api',
    version='0.1',
    description='browse otr torrent tracker with top recordings',
    #doc='/doc/',
    # All API metadatas
    authorizations=authorizations,
    #serve_challenge_on_401 = True,
    #catch_all_404s = True,
)

""" Initialize flask-restplus api ----------------------------------------------
"""
api.add_namespace(recording_ns)
api.add_namespace(push_ns)
api.add_namespace(dev_ns)

""" global error handling ------------------------------------------------------
"""
@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not app.config['DEBUG']:
        return {'message': message}, 500


