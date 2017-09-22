from flask import g, abort
from flask_httpauth import HTTPBasicAuth

from config import config, log

""" HTTP Authentification  """

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
def verify_password(client_id, password):

    client = next((client for client in config['APPLICATION_CLIENTS'] if client['ID'] == client_id), False)

    if client:
        """ verify by clientid """
        g.clientrole = client['ROLE']
        log.debug('client identified with role {}'.format(g.clientrole))
        return True
    else:
        return False



