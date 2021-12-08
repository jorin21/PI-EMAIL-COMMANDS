from dotenv import load_dotenv
from email.header import decode_header
from time import sleep
from wakeonlan import send_magic_packet
import paramiko
import imaplib
import email
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
load_dotenv('./.env')

# variables
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
imap_url = os.getenv('IMAPS')
MAC = os.getenv('MACA')
serv = os.getenv('SERV')
SSHuser = os.getenv('SSHuser')
SSHpass = os.getenv('SSHpass')
auth = str('User not Authenticated')

# authorized users and their identities 
users = {
    'jorgeeavila1@gmail.com' : 'Jorge Avila'
}


# commands
def ping(From):
    if From in users.keys():
        print('pong')
    else:
        auth
def turnon(From):
    if From in users.keys():
        print('Waking PC')
        send_magic_packet(MAC)
def turnoff(From):
    if From in users.keys():
        print('Sleeping PC')
        ssh.connect(serv, username=SSHuser, password=SSHpass)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('shutdown -s -f -t 5')
        
    else:
        auth
def stop(From):
    if From in users.keys():
        print('Stopping Crontab Updates')
        os.system('cmd /c "ping localhost"')
def restart(From):
    'restart code here'





    
        


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
                        
                        #command handler
                        if subject == 'wakepc':
                            turnon(From)
                        elif subject == 'sleeppc':
                            turnoff(From)
                        elif subject == 'ping':
                            ping(From)
                        elif subject == 'stopscr':
                            stop(From)
                        elif subject == 'restartpc':
                            restart(From)
                        else:
                            print('Command is not Found. Please try again!')
                        

                    elif 'attachment' in c_dispo:
                        print('Email contains attachment, Cannot Run Commands')
else:
    print("No New Messages")
    sleep(2)



        
# raw = email.message_from_bytes(msg[0][1])
# print(get_body(raw))


con.close()
con.logout()


