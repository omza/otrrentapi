""" flask imports """
from flask import (
    render_template, 
    Blueprint, 
    session, 
    request,
    g
    )

""" configuration """
from config import config, log
import os
from datetime import datetime


""" define blueprint """
otrrentwww = Blueprint('www', __name__, template_folder='templates')


""" view to top recordings """        
@otrrentwww.route('/')
def index():

    """ render platform template """
    return render_template('index.html')

