from flask import g, session, abort
from flask_httpauth import HTTPBasicAuth
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer, 
    BadSignature, 
    SignatureExpired)

""" import log and config """
from config import config, log

""" import & Init storage """
from azurestorage.tablemodels import User
from azurestorage import db

db.register_model(User())

""" HTTP Authentification  """
authorizations = {
    'basicauth': {
        'type': 'basic',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

""" handle token """
def generate_auth_token(user, expiration = 600):
    s = Serializer(config['SECRET_KEY'], expires_in = expiration)
    token = s.dumps({'PartitionKey': user.PartitionKey, 'RowKey': user.RowKey })
    token = token.decode('ascii')
    return token

def verify_auth_token(token):
    s = Serializer(config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None # valid token, but expired
    except BadSignature:
        return None # invalid token

    user = db.get(User(PartitionKey=data['PartitionKey'], RowKey= data['RowKey']))
    
    if db.exists(user):
        return user
    else:
        return None

basicauth = HTTPBasicAuth()

@basicauth.error_handler
def auth_error():
    log.debug('Authentification error callback')
    abort(401, 'Missing Authentification or wrong credentials')
    return

@basicauth.verify_password
def verify_password(clientid_or_token, fingerprint):
    
    # first try to authenticate by token
    user = verify_auth_token(clientid_or_token)
    
    if not user:     
        # try to authenticate with username/password
        user = db.get(User(PartitionKey=clientid_or_token, RowKey= fingerprint))
        if not db.exists(user):
            return False
    
    """ retrieve user and set global """
    g.user = user
    session['authtoken'] = generate_auth_token(user)

    """ verify by clientid """
    if user.ProUser:
        g.clientrole = 'PRO'
    else:
        g.clientrole = 'BASIC'
    log.debug('client identified with role {}'.format(g.clientrole))

    return True




