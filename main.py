from dotenv import load_dotenv
from email.header import decode_header
from time import sleep
from wakeonlan import send_magic_packet
from datetime import datetime
import smtplib, ssl
import paramiko
import imaplib
import email
import os
import subprocess
import random

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
load_dotenv("/home/pi/PI-EMAIL-COMMANDS/.env")

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
week = datetime.now().strftime('%U')

# authorized users and their identities 
users = {
    'jorgeeavila1@gmail.com' : 'Jorge Avila',
}










# code to check week and generate new word every week
with open('/home/pi/PI-EMAIL-COMMANDS/timepass.txt', 'r') as read_time:
    week_DB = read_time.read(2) # opens and reads the first two characters to check the week
    
    if week != week_DB: # if the current week is not equal to the DB file, then begin the change of the line and passphrase
        print('New Week, Changing Line and Passphrase\n-----------')
        r = open('/home/pi/PI-EMAIL-COMMANDS/words.txt').read().splitlines()

        word = random.choice(r) # chooses a random word from the word bank
        line = random.randrange(5)


        # Sends email to authorized users with new code and line
        message = f"""Subject: New Passcode and Line

        New Line #: {line + 1} 
        New Word: {word} 

        """
        for user in users.keys():
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(sserv, port, context=context) as server:
                server.login(username, password)
                server.sendmail(username, user, message)



        print(f'New Line #: {line + 1}')
        print(f'New Word: {word}\n-----------')

        # opens the file as write and rewrites the file with current week and new passphrase
        with open('/home/pi/PI-EMAIL-COMMANDS/timepass.txt', 'w') as txt:
            txt.write(f'{week} ; {word} ; {line}')


# reads log file for line number and passphrase
with open('/home/pi/PI-EMAIL-COMMANDS/timepass.txt', 'r') as txt:
    txt_r = txt.read().split(';')
    line = int(txt_r[2].strip())
    passc = txt_r[1].strip()


# command handler v2
class commandHandler:
    def __init__(self,subject,From,body):
        #defines subject and from in the class
        self.subject = subject
        self.From = From
        self.body = body.split('\n')

        
        #used to check if any command ran properly
        self.tst = 0
    def check(self,func_name): # function used to check subject and from func_name would be the command name in the email
        if self.subject == func_name:
            self.tst = 1

            if self.body[line] == passc:
                if self.From in users.keys():
                    return True
                else:
                    print('User not Authenticated')
                    return False
            else:
                print('Incorrect Passphrase or Line')

    #commands start here
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

    #commands end here
    def run(self): #run function for easy addition of commands to both multipart and single part emails
        #add commands here
        self.ping()
        self.turnon()
        self.turnoff()
        self.stop()
        self.restart()


        # checks if any command was found
        if self.tst != 1:
            print('command not found, please try again')





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

            #defines cH object and passes subject,From
            

            if msg.is_multipart():
                for part in msg.walk():
                    c_type = part.get_content_type()
                    c_dispo = str(part.get('Content-Disposition'))

                    if c_type == 'text/plain' and 'attachment' not in c_dispo:
                        body = part.get_payload(decode=True).decode()
                        
                        #run commandhandler
                        cH = commandHandler(subject,From,body)
                        cH.run()
            
                        

                    elif 'attachment' in c_dispo:
                        print('Email contains attachment, Cannot Run Commands')

            else: #if not multipart
                body = msg.get_payload(decode=True).decode()
                cH = commandHandler(subject,From,body)
                cH.run()
else:
    print("No New Messages")
    sleep(2)



        
# raw = email.message_from_bytes(msg[0][1])
# print(get_body(raw))


con.close()
con.logout()


