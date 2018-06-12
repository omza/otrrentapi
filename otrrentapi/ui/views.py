""" flask imports """
from flask import (
    render_template, 
    Blueprint, 
    session, 
    request,
    g,
    redirect,
    url_for
    )
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, 
    StringField, 
    PasswordField, 
    IntegerField,
    SelectField,
    validators
    )
from wtforms.widgets import PasswordInput

""" configuration """
from config import config, log
from helpers.helper import Message, test_ftpconnection, safe_cast
import os
from datetime import datetime
from functools import wraps

""" import & Init storage """
from azurestorage.wrapper import StorageTableCollection
from azurestorage.queuemodels import PushMessage, PushVideoMessage
from azurestorage.tablemodels import Recording, Torrent, User, History
from azurestorage import db
from azurestorage import queue

db.register_model(User())
db.register_model(History())
db.register_model(Recording())
db.register_model(Torrent())
queue.register_model(PushMessage())
queue.register_model(PushVideoMessage())


""" define blueprint """
otrrentui = Blueprint('ui', __name__, template_folder='templates', url_prefix = '/ui')

""" Settings wtf Forms """
class Settings(FlaskForm):
    PushVideo = BooleanField('Video pushen?')

    OtrUser = StringField('OTR User', validators=[validators.Email()])
    OtrPassword = StringField('OTR Password', widget=PasswordInput(hide_value=False))
    UseCutlist = BooleanField('Schnittliste verwenden?')
    #UseSubfolder = BooleanField('Use Cutlist for decoding?')

    Protocol = SelectField('Protokoll', validators=[validators.DataRequired()], choices=[('ftp', 'ftp'),('sftp', 'sftp')])
    Server = StringField('ftp Server', [validators.DataRequired()])
    Port = IntegerField('Port', [validators.DataRequired()])
    FtpUser = StringField('ftp User', [validators.DataRequired(), validators.Length(min=5, max=35)])
    FtpPassword = StringField('ftp Password', widget=PasswordInput(hide_value=False))
    ServerPath = StringField('Pfad', [validators.DataRequired(), validators.Length(min=1, max=35)])

@otrrentui.before_request
def beforerequestlogic():

    """ parse request data """
    g.platform = str.lower(request.args.get('cordovaplatform', request.user_agent.platform))
    g.clientid = request.args.get('clientid', config['APPLICATION_CLIENT_ID'])
    g.deviceuuid = request.args.get('deviceuuid', '')

    """ user = default """
    g.user = None

    """ set platform """
    if not g.platform in ['android','ios']:
        g.platform = config['APPLICATION_UI_DEFAULT']

    """ message """
    messageid = safe_cast(request.args.get('messageid', 0), int)
    g.message = Message()
    g.message.text = 'Entschuldigung! Diese Funktion wird noch entwickelt und steht in dieser Verion von otrrent noch nicht zu Verfügung.'
    
    if messageid == 1:
        g.message.header = 'Bewerten Sie otrrent'
        g.message.error = True    
        g.message.show = True
    
    elif messageid == 2:
        g.message.header = 'Nutzen Sie otrrent Werbefrei!'
        g.message.error = True    
        g.message.show = True

    elif messageid == 3:
        g.message.header = 'Nutzen Sie otrrent als Pro-User!'
        g.message.error = True    
        g.message.show = True

    elif messageid == 4:
        log.debug(messageid)
        g.message.header = 'Fehler'
        g.message.text = 'Bitte nutzen Sie die otrrent App! Sie sind nicht eingelogged'
        g.message.error = True    
        g.message.show = True


""" decorators """
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """ request user """
        
        if g.deviceuuid == '' or g.clientid == '':
            g.user = None

        else:
            loginuser = db.get(User(PartitionKey=g.clientid, RowKey=g.deviceuuid))

            """ user exists ? Create a new and  """
            if not db.exists(loginuser):
                loginuser.created = datetime.now()
                db.insert(loginuser)
            
            """ login user """
            g.user = loginuser
 
        return f(*args, **kwargs)
    return decorated_function

#
# ------------------------------------------------------------------------------------------------------------------------
#            
@otrrentui.route('/')
def index():
    """ retrieve top recordings with filters """
       
    #get toplist
    toplist = StorageTableCollection('recordings', "PartitionKey eq 'top'")
    toplist = db.query(toplist)
    toplist.sort(key = lambda item: item.beginn, reverse = True)

    for item in toplist:
        item['startdate'] = item.beginn.strftime('%d.%m.%Y')
        item['starttime'] = item.beginn.strftime('%H:%M')
        item['previewimagelink'] = item['previewimagelink'].replace('http://','https://',1)
        if not 'torrentCount' in item:
            item['torrentCount'] = 0


    """ render platform template """
    pathtemplate = g.platform + '/' + 'index.html'
    return render_template(pathtemplate, title = 'OTR Top Aufnahmen', pagetitle='index', items=toplist,
                            message=g.message)

#
# ------------------------------------------------------------------------------------------------------------------------
#
@otrrentui.route('/<int:epgid>', methods=['GET', 'POST'])
@login_required
def details(epgid):
    """ request top recording detail data """

    """ logging """
    log.info('select all details for recording: {!s} with method {!s}'.format(epgid, request.method))

    """ determine template & messages """
    pathtemplate = g.platform + '/' + 'details.html'

    #get message
    message = g.message
    g.pop('message')

    """ retrieve recording from storage """
    recording = db.get(Recording(PartitionKey = 'top', RowKey = str(epgid)))

    """ show details including all torrents """
    if not db.exists(recording):
        return index()

    recording.Torrents = db.query(recording.Torrents)
    recording.startdate = recording.beginn.strftime('%d.%m.%Y')
    recording.starttime = recording.beginn.strftime('%H:%M')
    recording.previewimagelink = recording.previewimagelink.replace('http://','https://',1)

    if request.method == 'POST':

        """ retrieve Form Data """
        data = request.form.to_dict()
        log.debug(data)

        """ post method = push only available for logged in users """
        if not g.user:
            message.show = True
            message.error = True
            message.header = 'Fehler'
            message.text = 'Bitte loggen Sie sich ein!'
        
        elif (not g.user.ProUser) and (g.user.PushVideo):
            message.show = True
            message.error = True
            message.header = 'Fehler'
            message.text = 'Um Videos zu decodieren müssen Sie Pro Status haben!'

        elif ExistsHistory(g.user.RowKey, epgid): 
            """ already in History ? """
            message.show = True
            message.error = True
            message.header = 'Fehler'
            message.text = 'Sie haben diese Aufnahme bereits erfolgreich gepushed!'

        elif (g.user.PushVideo):           
            """ push video """
            job, errormessage = PushVideo(epgid, data['Resolution'], data['TorrentFile'], data['TorrentLink'], g.user) 
            if not job:
                message.show = True
                message.error = True
                message.header = 'Fehler'
                message.text = errormessage
            else:
                """ success """
                message.show = True
                message.header = 'Erfolg'
                message.text = '{!s} wird heruntergeladen, decodiert und danach an Ihren Endpoint gepushed. Die Aufgabe {!s} wurde dazu erfolgreich angelegt'.format(job.sourcefile, job.id)
                
                """ add history """
                AddHistory(g.user, 
                           job.id, 'video', epgid, 
                           recording.beginn, recording.sender, recording.titel, recording.genre, recording.previewimagelink, data['Resolution'], 
                           job.sourcefile,
                           request.remote_addr, request.user_agent.platform,
                           request.user_agent.browser,
                           request.user_agent.version,
                           request.user_agent.language)                          

        else:           
            """ push torrent """
            job, errormessage = PushTorrent(epgid, data['Resolution'], data['TorrentFile'], data['TorrentLink'], g.user) 
            if not job:
                message.show = True
                message.error = True
                message.header = 'Fehler'
                message.text = errormessage
            else:
                """ success """
                message.show = True
                message.header = 'Erfolg'
                message.text = '{!s} wird heruntergeladen und an Ihren Endpoint gepushed. Die Aufgabe {!s} wurde dazu erfolgreich angelegt'.format(job.sourcefile, job.id)

                """ add history """
                AddHistory(g.user, 
                           job.id, 'torrent', 
                           epgid, 
                           recording.beginn, 
                           recording.sender, 
                           recording.titel, 
                           recording.genre, 
                           recording.previewimagelink,
                           data['Resolution'],
                           job.sourcefile,
                           request.remote_addr,
                           request.user_agent.platform,
                           request.user_agent.browser,
                           request.user_agent.version,
                           request.user_agent.language)     

    """ render platform template """
    return render_template(pathtemplate,  
                            title = 'OTR Aufnahme Details', 
                            pagetitle='details', 
                            item=recording,
                            message=message)

#
# ------------------------------------------------------------------------------------------------------------------------
#
@otrrentui.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """ validate settings form  at POST request """

    if not g.user:
        return redirect(url_for('ui.index',messageid=4))



    """ get request data """
    form = Settings()

    """ init values in get method """
    if form.validate_on_submit() or form.is_submitted(): 

        """ save form data to userprofile """
        if (g.user.PushVideo != form.PushVideo.data):
            g.user.PushVideo = form.PushVideo.data
            
        if (g.user.OtrUser != form.OtrUser.data):
            g.user.OtrUser = form.OtrUser.data
            
        if (g.user.UseCutlist != form.UseCutlist.data):
            g.user.UseCutlist = form.UseCutlist.data
            
        if (g.user.Protocol != form.Protocol.data):
            g.user.Protocol = form.Protocol.data
            g.user.FtpConnectionChecked = False
            
        if (g.user.Server != form.Server.data):
            g.user.Server = form.Server.data
            g.user.FtpConnectionChecked = False
            
        if (g.user.Port != form.Port.data):
            g.user.Port = form.Port.data
            g.user.FtpConnectionChecked = False
            
        if (g.user.FtpUser != form.FtpUser.data):
            g.user.FtpUser = form.FtpUser.data
            g.user.FtpConnectionChecked = False

        if (g.user.ServerPath != form.ServerPath.data):
            g.user.ServerPath = form.ServerPath.data
            g.user.FtpConnectionChecked = False

        if (form.OtrPassword.data not in ['*****']) and (g.user.OtrPassword != form.OtrPassword.data):
            g.user.OtrPassword = form.OtrPassword.data

        if (form.FtpPassword.data not in ['*****']) and (g.user.FtpPassword != form.FtpPassword.data):
            g.user.FtpPassword = form.FtpPassword.data
            g.user.FtpConnectionChecked = False

            
        """ check ftp Connection """
        if not g.user.FtpConnectionChecked:
            g.user.FtpConnectionChecked, validftpmessage = test_ftpconnection(g.user.Server, g.user.Port, g.user.FtpUser, g.user.FtpPassword, g.user.ServerPath)
                
            if not g.user.FtpConnectionChecked:
                log.error(validftpmessage)


        """ check otr credentials """
        if not g.user.OtrCredentialsChecked:
            pass

        """ update user """
        g.user.updated = datetime.now()
        db.insert(g.user)        

    else:
        form.PushVideo.data = g.user.PushVideo
        form.OtrUser.data = g.user.OtrUser

        if g.user.OtrPassword != '':
            form.OtrPassword.data = '*****'
        else:
            form.OtrPassword.data = ''

        form.UseCutlist.data = g.user.UseCutlist
        form.Protocol.data = g.user.Protocol
        form.Server.data = g.user.Server
        form.Port.data = g.user.Port
        form.FtpUser.data = g.user.FtpUser
            
        if g.user.FtpPassword != '':
            form.FtpPassword.data = '*****'
        else:
            form.FtpPassword.data = ''

        form.ServerPath.data = g.user.ServerPath

    """ return """
    pathtemplate = g.platform + '/' + 'settings.html'
    return render_template(pathtemplate, title = 'Einstellungen', pagetitle='settings', form=form, User=g.user)

#
# ------------------------------------------------------------------------------------------------------------------------
#
@otrrentui.route('/history')
@login_required
def history():
    """ retrieve top recordings with filters """

    if not g.user:
        return redirect(url_for('ui.index', messageid=4))

    historylist = StorageTableCollection('history', "PartitionKey eq '" + g.user.RowKey + "'")
    historylist = db.query(historylist)
    historylist.sort(key = lambda item: item.created, reverse = True)

    for item in historylist:
        item['startdate'] = item.beginn.strftime('%d.%m.%Y')
        item['starttime'] = item.beginn.strftime('%H:%M')
        item['createdate'] = item.created.strftime('%d.%m.%Y')
        item['updatedate'] = item.updated.strftime('%d.%m.%Y %H:%M')
        item['previewimagelink'] = item['previewimagelink'].replace('http://','https://',1)


    """ render platform template """
    pathtemplate = g.platform + '/' + 'history.html'
    return render_template(pathtemplate, title = 'Verlauf', pagetitle='history', items=historylist)

#
# ------------------------------------------------------------------------------------------------------------------------
#
@otrrentui.route('/about')
def about():

    #get message
    message = g.message
    log.debug(message.header)
    g.pop('message')

    """ render platform template """
    pathtemplate = g.platform + '/' + 'about.html'
    return render_template(pathtemplate, title = 'Über', pagetitle='about', message=message)



#
# ------------------------------------------------------------------------------------------------------------------------
#
def PushTorrent(epgid, resolution, sourcefile, sourcelink, user:User):
    """ create a push queue message for torrent push """   
    ErrorMessage = ''
    job = None
    
    """ further validations:
        test connection to ftp destination server
    """
    validftp, validftpmessage = test_ftpconnection(user.Server, user.Port, user.FtpUser, user.FtpPassword, user.ServerPath)
    if not validftp:
        log.error(validftpmessage)
        ErrorMessage = validftpmessage

    else:
        """ init a PushMessage instance and put it into queue """
        job = queue.put(PushMessage(
                epgid=epgid,
                resolution=resolution,
                sourcefile=sourcefile,
                sourcelink=sourcelink,
                protocol=user.Protocol,
                server=user.Server,
                port=user.Port,
                user=user.FtpUser,
                password=user.FtpPassword,
                destpath=user.ServerPath))
        
        if job is None:
            ErrorMessage = 'Fehler beim Erstellen der Push Aufgabe'

        else:
            """ success """
            log.debug('mesage input: {!s}, {!s}, {!s}'.format(job.getmessage(), job.id, job.insertion_time))

    return job, ErrorMessage

def PushVideo(epgid, resolution, sourcefile, sourcelink, user:User):
    """ create a push queue message for torrent push """   
    ErrorMessage = ''
    job = None
    
    """ further validations:
        test connection to ftp destination server
    """
    validftp, validftpmessage = test_ftpconnection(user.Server, user.Port, user.FtpUser, user.FtpPassword, user.ServerPath)
    if not validftp:
        log.error(validftpmessage)
        ErrorMessage = validftpmessage

    else:
        """ init a PushMessage instance and put it into queue """
        
        """ update otrkey filename as output """
        otrkeyfile = os.path.splitext(os.path.basename(sourcelink))[0]
        videofile = os.path.splitext(os.path.basename(otrkeyfile))[0]        
        
        
        job = queue.put(PushVideoMessage(
                epgid=epgid,
                resolution=resolution,
                sourcefile=sourcefile,
                sourcelink=sourcelink,
                protocol=user.Protocol,
                server=user.Server,
                port=user.Port,
                user=user.FtpUser,
                password=user.FtpPassword,
                destpath=user.ServerPath,
                otrkeyfile=otrkeyfile,
                videofile=videofile,
                otruser=user.OtrUser,
                otrpassword=user.OtrPassword,
                usecutlist=user.UseCutlist,
                usesubfolder=user.UseSubfolder))
        
        if job is None:
            ErrorMessage = 'Fehler beim Erstellen der Push Aufgabe'

        else:
            """ success """
            log.debug('mesage input: {!s}, {!s}, {!s}'.format(job.getmessage(), job.id, job.insertion_time))

    return job, ErrorMessage

def AddHistory(user:User, taskid, tasktype, epgid, beginn, sender, titel, genre, previewimagelink, resolution, sourcefile, ip, platform, browser, version, language):
    
    """ handle history entries """
    history = History(PartitionKey = user.RowKey, RowKey = str(taskid))

    history.taskid = taskid
    history.tasktype = tasktype

    history.epgid = int(epgid)
    history.sourcefile = sourcefile
    history.beginn = beginn
    history.sender = sender
    history.titel = titel
    history.genre = genre    
    history.previewimagelink = previewimagelink
    history.resolution = resolution

    history.ip = ip
    history.platform = platform
    history.browser = browser
    history.version = version
    history.language = language

    history.status = 'new'
    history.created = datetime.now()
    history.updated = history.created
    db.insert(history)

def ExistsHistory(fingerprint, epgid ) -> bool:
    
    """ get job history for users fingerprint and epg id """
    historylist = StorageTableCollection('history', "PartitionKey eq '" + fingerprint + "'")
    historylist = db.query(historylist)

    identicalepgs = [item for item in historylist if item['epgid'] == int(epgid)]
    
    if len(identicalepgs) > 0:
        return True
    else:
        return False



