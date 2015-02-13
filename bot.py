#! /usr/bin/python
import sys
import socket
import string
import re

f = open('botlogin.dat')
global HOST, PORT, PASS, NICK, CHANNEL
HOST = "irc.twitch.tv"
PORT = 6667
PASS = f.readline()
NICK = f.readline()
f.close()
#TODO: Make a master file that takes name a runs a new instance of the bot

try:
    CHANNEL = sys.argv[1]
except:
    raise Exception("No stream input")

global readbuffer
readbuffer = ""

global username
username = ':(\w+)!'
global said
said = "PRIVMSG\s#.+:(.+)"

global s

global commands
commands = {}

def loadUserCommands(f):#get user's config file and load their commands checking chat
    global commands
    pass

def checkSpam(line, name):#TODO: t/o links, more
    pass

def checkSubs():
    pass

def checkCommands(line):#TODO: mod only commands and command cooldowns
    global commands

    pass

def connect():
    global s, readbuffer
    global HOST, PORT, PASS, NICK, CHANNEL

    s = socket.socket()
    s.settimeout(5.0)
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
        print "+Connected to #"+CHANNEL
        #print readbuffer
    except Exception as e:
        print "-Error: " + str(e)
        raise


def run():
    global readbuffer
    global username
    global said

    while True:
        try:
            readbuffer = readbuffer + s.recv(4096)
        except socket.timeout as e: #TODO: Put growing timeout (don't want to spam if twitch is down)
            connect()
        except Exception as e:
            print "-Error: " + str(e)
            raise
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
                    commands = checkCommands(chatLine)
                    spam = checkSpam(chatLine, name)
                    print name + ': ' + chatLine
                else:#TODO: Catch sub messages, have whatever message in response
                    #subResponse = checkSubs(line)
                    pass

loadUserCommands(CHANNEL)
connect()
run()
