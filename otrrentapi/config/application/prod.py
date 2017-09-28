# Flask settings
SERVER_NAME = None
DEBUG = True  # Do not use debug mode in production
PORT = None
HOST = None

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = True
BUNDLE_ERRORS = True

# ottrent settings
APPLICATION_PATH_LOG = '/usr/log/'
APPLICATION_LOGLEVEL_CONSOLE = 20 # debug 
APPLICATION_LOGLEVEL_FILE = 20 # debug
APPLICATION_LOG_LEVEL = 20 # Debug
APPLICATION_MAINLOGGER = 'otrrentapi'

# azure storage settings
AZURE_REQUIRE_ENCRYPTION = True
AZURE_KEY_IDENTIFIER = 'otrrentapi'


