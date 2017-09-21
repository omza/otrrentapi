from flask import g, abort
from flask_httpauth import HTTPBasicAuth



# Logger
import logging
log = logging.getLogger('diboardapi.' + __name__)

# HTTP Authentification
# --------------------------------------------------------------
authorizations = {
    'basicauth': {
        'type': 'basic',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}


basicauth = HTTPBasicAuth()

@basicauth.error_handler
def auth_error():
    log.debug('Authentification error callback')
    abort(401, 'Missing Authentification or wrong credentials')
    return

@basicauth.verify_password
def verify_password(username, password):

    """ verify by clientid """
    g.user = 'client-ID'
    return True

