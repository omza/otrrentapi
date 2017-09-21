""" 
    imports & globals
    -------------------------------------------------------------------------------
"""

import os
from sys import stdout

from flask import Flask
from api import otrrentapi

import logging
import logging.handlers

# Flask app instance
app = Flask(__name__)

"""
    App Configuration
    ------------------------------------------------------------------------------
"""    

# Load the default configuration
from config import config
app.config.update(config)


"""
    Logging Configuraion
    ---------------------------------------------------------------------------------
    formatter
"""
from config import log


# register blueprints api and manage
# --------------------------------------------------------
app.register_blueprint(otrrentapi)


# log App configuration/setting  if in debug mode
# --------------------------------------------------------
if app.debug:
    for key, value in app.config.items():
        if key.find('OTRRENTSERVER') >= 0:
            log.debug('{} = {!s}'.format(key, value))


# main
# -----------------------------------------------------------
if __name__ == '__main__':
    
    # run di.boards api app
    if app.config['SERVER_NAME'] is not None:
        app.run()
    else:
        app.run(host=app.config['HOST'], port = app.config['PORT'])
