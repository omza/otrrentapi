# imports & globals
# -------------------------------------------------------------
import os

from flask import Blueprint, json
from flask_restplus import Api

from api.recording import api as recording_ns
from api.task import api as task_ns

from auth import authorizations

""" configuration  & logging"""
from config import config, log


# register flask_restplus api and namespaces as blueprint
# --------------------------------------------------------------

otrrentapi = Blueprint('api', __name__, url_prefix='/api') # subdomain ='api')


api = Api(otrrentapi,
    title='otrrent api',
    version='0.1',
    #description='bring your real world bulletin board in digitial life',
    #doc='/doc/',
    # All API metadatas
    #authorizations=authorizations,
    #serve_challenge_on_401 = True,
    #catch_all_404s = True,
)

# Initialize flask-restplus api
# register di.boards api namespace
api.add_namespace(recording_ns)
api.add_namespace(task_ns)

# global error handling
# --------------------------------------------------------------
@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not app.config['DEBUG']:
        return {'message': message}, 500


