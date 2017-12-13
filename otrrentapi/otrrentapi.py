""" 
    imports & globals
    -------------------------------------------------------------------------------
"""

import os
from sys import stdout

from flask import Flask
from api import otrrentapi
from ui.views import otrrentui

import logging
import logging.handlers
from werkzeug.contrib.fixers import ProxyFix


# Flask app instance
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

"""
    App Configuration
    ------------------------------------------------------------------------------
"""    

# Load the default configuration
from config import config, log
app.config.update(config)

""" register blueprints api and manage --------------------------------------------------------  """
app.register_blueprint(otrrentapi)
app.register_blueprint(otrrentui)



# log App configuration/setting  if in debug mode
# --------------------------------------------------------
if app.debug:
    for key, value in app.config.items():
        if key.find('APPLICATION') >= 0:
            log.debug('{} = {!s}'.format(key, value))


# main
# -----------------------------------------------------------
if __name__ == '__main__':
    
    # run di.boards api app
    if app.config['SERVER_NAME'] is not None:
        app.run()
    else:
        app.run(host=app.config['HOST'], port = app.config['PORT'])
