from dotenv import load_dotenv
from email.header import decode_header
from time import sleep
from wakeonlan import send_magic_packet
import paramiko
import imaplib
import email
import os
import subprocess

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
load_dotenv("/home/pi/PI-EMAIL-COMMANDS/.env")

# variables
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
imap_url = os.getenv('IMAPS')
MAC = os.getenv('MACA')
serv = os.getenv('SERV')
SSHuser = os.getenv('SSHuser')
SSHpass = os.getenv('SSHpass')

# authorized users and their identities 
users = {
    'jorgeeavila1@gmail.com' : 'Jorge Avila'
}




# command handler v2
class commandHandler:
    def __init__(self,subject,From,body):
        #defines subject and from in the class
        self.subject = subject
        self.From = From
        self.body = body
        count = 1
        for line in self.body.split('\n'): #beginning of passphrase checker
            print(line)
            if count == 3:
                if line == 'passcod':
                    print('allow')
                else:
                    print('not allowed')
            count += 1

        #used to check if any command ran properly
        self.tst = 0
    def check(self,func_name): # function used to check subject and from func_name would be the command name in the email
        if self.subject == func_name:
            if self.From in users.keys():
                self.tst = 1
                return True
            else:
                print('User not Authenticated')
                return False

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
            cmd = 'ping -c 2 localhost'
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


        # checks if any command was ran
        if self.tst != 1:
            print('command not found please try again')


# commandHandler('testing','1','line 1 \nline 2\npasscode\n').run()


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


