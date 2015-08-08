#! /usr/bin/python
import sys, socket, string, re, os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from webapp import Command

global HOST, PORT, PASS, NICK, CHANNEL, db
HOST = "irc.twitch.tv"
PORT = 6667
PASS = os.environ['bot_pass']
NICK = 'zojibot'

app = Flask(__name__) #TODO: get some real sqlalchemy in here
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]#'postgresql://localhost/test.db'
db = SQLAlchemy(app)


try:
    CHANNEL = sys.argv[1]
except:
    raise Exception("No stream input")

global readbuffer, timecount
readbuffer = ""
timecount = 1

global username
username = ':(\w+)!'
global said
said = "PRIVMSG\s#.+:(.+)"

global s

global commands
commands = {}

def loadUserCommands(f):#get user's config file and load their commands checking chat
    global commands
    rawCommands = Command.query.filter_by(username=f)
    commandRE = 'Command:\s(.+)\sResponse:'
    responseRE = 'Response:\s(.+)\sCommand\sID'
    for line in rawCommands:
        #print 'Grabbing in: '+repr(line)
        cre = re.search(commandRE, repr(line)).group(1)
        rre = re.search(responseRE, repr(line)).group(1)
        #print 'Command: '+cre
        #print 'Response: '+rre
        commands[cre] = rre
        #print 'Got '+commands[re.search(commandRE, repr(line))]+' for '+re.search(commandRE, repr(line))


def checkSpam(line, name):#TODO: t/o links, more
    pass

def checkSubs():
    pass

def checkCommands(readline):#TODO: mod only commands and command cooldowns
    global commands, db

    #2 ways to do it, either check whole msg, or have the command be the only thing allowed
    #going to do only thing allowed, much much faster
    #print 'Checking commands: '+readline
    #print 'Checking command data structure: '+commands[readline]
    print type(readline) is str
    if readline in commands:
        sendMessage(commands[readline])
    else:
        (first, sep, after) = readline.partition(' ')
        if first == '!edit':
            (first, sep, after) = first.partition(' ')
            print 'Editing command in the database'
            com = Command.query.filter_by(username=CHANNEL, comm=first)
            com.editCommand(after)
            db.session.commit()




def connect():
    global s, readbuffer, timecount
    global HOST, PORT, PASS, NICK, CHANNEL

    s = socket.socket()
    s.settimeout(10.0*timecount)
    try:
        s.connect((HOST, PORT))
        s.send("PASS %s\r\n" % PASS)
        s.send("NICK %s\r\n" % NICK)
        print "+Connected to Twitch chat"
        s.send("JOIN #%s\r\n" % CHANNEL)

    except Exception as e:
        print "-Error: " + str(e)
        raise
    print "+Connecting to " +CHANNEL

    try:
        readbuffer = readbuffer + s.recv(4096)
        #s.send('PRIVMSG #%s hi\r\n' % CHANNEL)
        print "+Connected to #"+CHANNEL
        #print readbuffer
    except Exception as e:
        print "-Error: " + str(e)
        raise

def sendMessage(m):
    global s, CHANNEL
    msg = "PRIVMSG #"+CHANNEL+" :"+m+"\r\n"
    print 'trying to say '+msg
    s.send(msg)
    #s.send('HELPOP USERCMDS\r\n')

def run():
    global readbuffer, username, said, s, timecount
    while True:
        try:
            readbuffer = readbuffer + s.recv(4096)
        except socket.timeout as e: #TODO: Put growing timeout (don't want to spam if twitch is down)
            if timecount < 20:
                timecount += 1
            connect()
        except Exception as e:
            print "-Error: " + str(e)
            raise
        timecount = 1
        temp = readbuffer.split("\n")
        last = temp.pop()
        #print last
        #print temp
        readbuffer = last


        for line in temp:
            reg = re.search(username, line)
            #print 'original match ' + line
            if reg != None:
                name = reg.group(1)
                #print 'matching ' + line
                regchat = re.search(said, line)
                if regchat != None:
                    chatLine = regchat.group(1)
                    checkCommands(chatLine.rstrip())
                    spam = checkSpam(chatLine, name)
                    print name + ': ' + chatLine
                else:#TODO: Catch sub messages, have whatever message in response
                    #subResponse = checkSubs(line)
                    pass

loadUserCommands(CHANNEL)
connect()
run()
