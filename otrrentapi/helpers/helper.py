""" helper """
import datetime
import ftplib


def safe_cast(val, to_type, default=None, dformat=''):
    try:
        result = default
        if to_type in [datetime.datetime, datetime.date]:
            if type(val) == to_type:
                val = val.strftime(dformat)
           
            result = to_type.strptime(val, dformat)
        
        elif to_type is bool:
            result = str(val).lower() in ("yes", "true", "t", "1")
        
        elif to_type is str:
            if (isinstance(val, datetime.datetime) or isinstance(val, datetime.date)):
                result = str(val).strftime(dformat)
            else:
                result = str(val)
        else:
            result = to_type(val)

        return result
        
    except (ValueError, TypeError):
        return default

def test_ftpconnection(server, port, user, password, path):
    try:
                
        """ login to ftp server """
        ftp = ftplib.FTP()

        ftp.connect(server, port)
        ftp.login(user=user, passwd=password)
      
        """ check fpt_path exist ? """
        ftp.cwd(path)

        """ logout ftp session """
        ftp.quit()

        """ return """
        return True, None
                
    except ftplib.all_errors as e:
        return False, 'Error in ftp login ({!s}:{!s}) = {!s}'.format(server, port, e)

class Message():

    def __init__(self, show:bool=False, error:bool=False, header:str = '', text:str = '', code:int = 0):
        self.show = show
        self.error = error
        self.header = header
        self.text = text
        self.code = code
        pass

      



        