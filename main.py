from dotenv import load_dotenv
from email.header import decode_header
from time import sleep
from wakeonlan import send_magic_packet
from datetime import datetime
from dropbox import DropboxOAuth2FlowNoRedirect
import smtplib, ssl
import paramiko
import imaplib
import email
import os
import subprocess
import random
import inspect
import dropbox
            
#loads some dependencies
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
load_dotenv("./.env")

# variables
username = os.getenv('USERNAME1')
password = os.getenv('PASSWORD')
imap_url = os.getenv('IMAPS')
MAC = os.getenv('MACA')
serv = os.getenv('SERV')
sserv = os.getenv('SMTPS')
port = os.getenv('SMTPPORT')
SSHuser = os.getenv('SSHuser')
SSHpass = os.getenv('SSHpass')
APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')


week = datetime.now().strftime('%U')


# authorized users and their identities 
users = {
    'jorgeeavila1@gmail.com' : 'Jorge Avila',
}

#defines a function that starts an SMTP connection to send mail
def sendmail(message,user):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(sserv, port, context=context) as server:
        server.login(username, password)
        server.sendmail(username, user, message)


# defines function used to read email and whether to run the commandHandler
def readmail(run_commandHandler):
    #connection
    con = imaplib.IMAP4_SSL(imap_url)
    con.login(username, password)


    # email setup
    status, emails = con.select('INBOX')
    emails = int(emails[0])
    Umail = con.search(None, 'UnSeen')[1][0].split()
    UnSeen = len(Umail)

    # email fetch
    stat, msg = con.fetch(str(emails), "(RFC822)")
    Rmail = con.search(None, 'UnSeen')[1][0].split()
    Read = len(Rmail)
    
    # checks for any new emails
    if UnSeen > Read:
        for res in msg:
            if isinstance(res, tuple):
                msg = email.message_from_bytes(res[1])

                
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding)

                From = decode_header(msg.get('From'))
                if isinstance(From, bytes):
                    From = From.decode(encoding)
                    
                From = From[0][0].split('<')
                From = From[1][:-1]
                



                if msg.is_multipart():
                    for part in msg.walk():
                        c_type = part.get_content_type()
                        c_dispo = str(part.get('Content-Disposition'))

                        if c_type == 'text/plain' and 'attachment' not in c_dispo:
                            body = part.get_payload(decode=True).decode()
                            
                            #run commandhandler if needed
                            if run_commandHandler:
                                cH = commandHandler(subject,From,body)
                                cH.run()
                            
                            return subject.strip(), From, body

                        elif 'attachment' in c_dispo:
                            print('Email contains attachment, Cannot Run Commands')

                else: #if not multipart
                    body = msg.get_payload(decode=True).decode()
                    if run_commandHandler: #run commandhandler if needed
                        cH = commandHandler(subject,From,body)
                        cH.run() #runs commandHandler with no multipart message

                    return subject.strip(), From, body


    else:
        print("No New Messages")
        sleep(2)
        return 'None', None, None
        

    con.close()
    con.logout()




# code to check week and generate new word every week
with open('timepass.txt', 'r') as read_time:
    week_DB = read_time.read(2) # opens and reads the first two characters to check the week
    
    
    if week != week_DB: # if the current week is not equal to the DB file, then begin the change of the line and passphrase
        print('New Week, Changing Line and Passphrase\n-----------')
        r = open('words.txt').read().splitlines()

        word = random.choice(r) # chooses a random word from the word bank
        line = random.randrange(5)
        auth = read_time.read().split(';')[3].strip()
        
        # Sends email to authorized users with new code and line
        message = f"""Subject: New Passcode and Line

        New Line #: {line + 1} 
        New Word: {word} 

        """
        for user in users.keys():
            sendmail(message,user)

        print(f'New Line #: {line + 1}')
        print(f'New Word: {word}\n-----------')

        # opens the file as write and rewrites the file with current week and new passphrase
        with open('timepass.txt', 'w') as txt:
            txt.write(f'{week} ; {word} ; {line} ; {auth}')

        
# reads log file for line number, passphrase, and Dropbox Auth Code
with open('timepass.txt', 'r') as txt:
    txt_r = txt.read().split(';')
    line = int(txt_r[2].strip())
    passc = txt_r[1].strip()
    auth = txt_r[3].strip()

# command handler v2
class commandHandler:
    def __init__(self,subject,From,body):
        #defines subject and from in the class
        self.subject = subject
        self.From = From
        self.body = body

        
        #used to check if any command ran properly
        self.tst = 0

    def check(self,cmd_name): # function used to check subject and from, cmd_name would be the command name in the email
        if self.subject == cmd_name:
            self.tst = 1

            if self.From in users.keys():
                self.body = self.body.split('\n')

                if self.body[line].strip() == passc:
                    return True

                else:
                    print('Incorrect Passphrase or Line')

            else:
                print('User not Authenticated')
                message = f"""Subject: Unauthorized Login Attempt

Login Email: {self.From}
Attempted Command: {self.subject}
Email Body:
{self.body}"""
                
                for user in users.keys():
                    sendmail(message,user)
                return False
                

#  __                                     #
# /   _ __ __  _ __  _| _    |_| _  __ _  #
# \__(_)||||||(_|| |(_|_>    | |(/_ | (/_ #
#                                         #


    def ping(self):
        if self.check('ping'):
            print('pong')
            
    def turnon(self):
        if self.check('wakepc'):
            print('Waking PC')
            send_magic_packet(MAC)
        
    def turnoff(self):
        if self.check('sleeppc'):
            print('Sleeping PC')
            ssh.connect(serv, username=SSHuser, password=SSHpass)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('shutdown -s -f -t 5')    
        
    def stop(self):
        if self.check('stopscr'):
            print('Stopping Crontab Updates')
            cmd = 'crontab -r'
            process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()

    def restart(self):
        if self.check('restpc'):
            'restart code here'

    def change(self):
        if self.check('changepass'):
            print('Changing Pass')
            message = "Subject: Password Change" \
                      "\nReply to this with new password on 6th line and passphrase"
            
            
            sendmail(message,self.From)
        elif self.check('Re: Password Change'):
            word = self.body[5].strip()
            print(f"Changing Pass to '{word}'")

            with open('timepass.txt', 'w') as newpass:
                newpass.write(f'{week} ; {word} ; {line} ; {auth}')

            with open('timepass.txt', 'r') as readpass:
                r = readpass.read().split(';')[1].strip()
            
            if r == word:
                print('Changed Pass Successfully')
            else:
                print('Something went wrong check the code')

    def sendfiles(self):
        if self.check('sendfiles'):
            try:
                    with dropbox.Dropbox(oauth2_access_token=auth) as dbx:
                        dbx.users_get_current_account()
                        print("Successfully set up client!")

            except Exception as e:
                print(e)
                print('need new API access token')

                


                auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

                authorize_url = auth_flow.start()
                print(authorize_url)
                message = """Subject: DropBox API Call

1. Go to %s
2. Click "Allow" (you might have to log in first).
3. Copy the authorization reply to this email with it""" %authorize_url

                sendmail(message, self.From)
            
                while True:
                    subject, From, body = readmail(run_commandHandler=False)
                                    
                    if subject == "Re: DropBox API Call":
                        body = body.split("\n")
                        auth_code = body[0].strip()

                        try:
                            oauth_result = auth_flow.finish(auth_code)
                        except Exception as e:
                            print('Error: %s' % (e,))
                            exit(1)

                        with open('timepass.txt', 'w') as newauth:
                            newauth.write(f'{week} ; {passc} ; {line} ; {oauth_result.access_token}')

                        with dropbox.Dropbox(oauth2_access_token=oauth_result.access_token) as dbx:
                            dbx.users_get_current_account()
                            print("Successfully set up client!")
                            break


#  __                         __       #
# /   _ __ __  _ __  _| _    |_ __  _| #
# \__(_)||||||(_|| |(_|_>    |__| |(_| #
#                                      #

    def run(self): #run function for easy addition of commands to both multipart and single part emails
        methods = inspect.getmembers(commandHandler, predicate=inspect.isfunction) #gets list of all methods in the class
        for method in methods: #runs each method in the list for the exception of the init run and check
            if method[0] != '__init__' and method[0] != 'run' and method[0] != 'check': 
                method[1](self)
                if self.tst == 1:
                    print(f'Ran {method[0]}')
                    self.tst = 2

        # checks if any command was found
        if self.tst < 1:
            print('command not found, please try again')




#readmail using the commandHandler
readmail(run_commandHandler=True)