from Globals import Persistent, HTMLFile, HTML
from socket import *
import Acquisition, sys, regex, string

#$Id: MailHost.py,v 1.4 1997/09/10 15:07:18 jeffrey Exp $ 
__version__ = "$Revision: 1.4 $"[11:-2]
smtpError = "SMTP Error"
MailHostError = "MailHost Error"

addForm=HTMLFile('MailHost/addMailHost_form')
def add(self, id='aMailHost', title='Some mail thing', smtp_host=None, 
        localhost='localhost', smtp_port=25, REQUEST):
    ' add a MailHost into the system '
    i=MailHost()            #create new mail host
    i.id=id                 #give it id
    i.title=title           #title
    i._init(localHost=localhost, smtpHost=smtp_host, smtpPort=smtp_port)
    self._setObject(id,i)   #register it
    return self.manage_main(self,REQUEST)   #and whatever this does..  :)


class MailHost(Persistent, Acquisition.Implicit):
    'a mailhost...?'
    manage=HTMLFile('MailHost/manageMailHost')
    index_html=HTMLFile('MailHost/mailHost')
    icon="MailHost/MailHost_icon.gif"
    
    def __init__(self):
        'nothing yet'
        pass

    def _init(self, localHost, smtpHost, smtpPort):
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
        self.sentMessages=0

    def manage_makeChanges(self, title, localHost, smtpHost, smtpPort):
        'make the changes'
        self.title=title
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
        return self.manage(self,REQUEST)
    
    def __log(self):
        self.sentMessages=self.sentMessages + 1

    def sendTemplate(trueself, self, messageTemplate, 
                     statusTemplate=None, mto=None, mfrom=None, REQUEST):
        'render a mail template, then send it...'
        mtemplate = getattr(self, messageTemplate)
        messageText = mtemplate(self, trueself.REQUEST)

        headers, message = newDecapitate(messageText)
        if mto: headers['to'] = mto
        if mfrom: headers['from'] = mfrom
        for requiredHeader in ('to', 'from', 'subject'):
            if not headers.has_key(requiredHeader):
                raise MailHostError,"Message missing SMTP Header '%s'"\
                % requiredHeader
        
        SendMail(trueself.smtpHost, trueself.smtpPort, 
                 trueself.localHost).send( 
                        mfrom=headers['from'], mto=headers['to'],
                        subj=headers['subject'], body=messageText
                        )

        self.__log()
        return ("sent","sent...")
        #return getattr(self,statusTemplate)(self, self.REQUEST, 
        #                                   messageText=message)
        
    def send(self, messageText, mto=None, mfrom=None):
        'send a rendered message'
        headers, message = newDecapitate(messageText)
        if mto: headers['to'] = mto
        if mfrom: headers['from'] = mfrom
        for requiredHeader in ('to', 'from', 'subject'):
            if not headers.has_key(requiredHeader):
                raise MailHostError,"Message missing SMTP Header '%s'"\
                % requiredHeader
    
        SendMail(self.smtpHost, self.smtpPort, self.localHost).send( 
                            mfrom=headers['from'], mto=headers['to'],
                            subj=headers['subject'], body=messageText)
                        
        self.__log()
        return ("sent","sent...")
        #return getattr(self,statusTemplate)(self, self.REQUEST, 
        #                                   messageText=message)

    def simple_send(self, mto, mfrom, subject, body):
        'like the simplist send or something'
        body="subject: %s\n\n%s" % (subject, body)
        SendMail(self.smtpHost, self.smtpPort, self.localHost).send( 
                        mfrom=mfrom, mto=mto, subj=subject, body=body)
        self.__log()
        return ("sent","sent...")
        
class SendMail:     
    def __init__(self, smtpHost, smtpPort, localHost="localhost"):
        self.conn = socket(AF_INET, SOCK_STREAM)
        self.conn.connect(smtpHost, smtpPort)
        self.conn.send("helo "+localHost+"\r\n")
        self._check('220')

    def __del__(self):
        self.close()

    def _check(self, lev='250'):
        data = self.conn.recv(1024)
        if data[:3] != lev:
            raise smtpError, "Expected %s, got %s from SMTP"%(lev, data[:3])

    def send(self, mfrom, mto, subj, body):
        self.conn.send("mail from:<%s>\n"%mfrom)
        self._check()
        if type(mto) == type([1,2]):
            for person in mto:
                self.conn.send("rcpt to:<%s>\n" % person)
                self._check()
        else:
            self.conn.send("rcpt to:<%s>\n"%mto)
            self._check()
        self.conn.send("data\n")
        self._check()
        self.conn.send(body)
        self.conn.send("\n.\n")
        self._check('354')

    def _close(self):
        self.conn.send("quit\n")
        self.conn.close()

def newDecapitate(message):
    blank_re =regex.compile('^[%s]+$' % string.whitespace)
    header_re=regex.symcomp('^\(<headerName>[^\0- <>:]+\):\(<headerText>.*\)$')
    
    linecount=0; headerDict={}
    maxwell=map(lambda x: string.strip(x),string.split(message,'\n'))

    for line in maxwell:
        if not line: break
        if blank_re.match(line) >= 0: break
        if header_re.match(line) >=0:
            headerDict[string.lower(header_re.group('headerName'))] =\
                        string.strip(header_re.group('headerText'))
        linecount=linecount+1
    
    body=string.join(maxwell[linecount:],'\n')
    return headerDict, body

def decapitate(message,
               header_re=regex.compile(
                    '\(\('
                      '[^\0- <>:]+:[^\n]*\n'
                    '\|'
                      '[ \t]+[^\0- ][^\n]*\n'
                    '\)+\)[ \t]*\n\([\0-\377]+\)'
                   ),
                  #r'(([^\0- <>:]+:[^\n]*\n|[ \t]+[^\0- ][^\n]*\n)+)[ \t]*\n([\0-\377]+)'
               space_re=regex.compile('\([ \t]+\)'),
               name_re=regex.compile('\([^\0- <>:]+\):\([^\n]*\)'),
               ):
    if header_re.match(message) < 0: return message

    headers, body = header_re.group(1,3)

    headers=string.split(headers,'\n')
    headerDict={}

    i=1
    while i < len(headers):
        if not headers[i]:
            del headers[i]
        elif space_re.match(headers[i]) >= 0:
            headers[i-1]="%s %s" % (headers[i-1],
                                    headers[i][len(space_re.group(1)):])
            del headers[i]
        else:
            i=i+1

    for i in range(len(headers)):
        if name_re.match(headers[i]) >= 0:
            k, v = name_re.group(1,2)
            k=string.lower(k); v=string.strip(v)
            headerDict[k]=v
        else:
            raise ValueError, 'Invalid Header (%d): %s ' % (i,headers[i])

    if headerDict.has_key('to'):
        headerDict['to']=map(
            lambda x: string.strip(x),
            string.split(headerDict['to'], ',')
            )

    return (headerDict, body)

#$Log: MailHost.py,v $
#Revision 1.4  1997/09/10 15:07:18  jeffrey
#and converted tabs back to spaces in source..  sorry!
##