#! /usr/bin/python
import sys
import socket
import string
import re
#import file

f = open('botlogin.dat')
global HOST, PORT, PASS, NICK, CHANNEL
HOST = "irc.twitch.tv"
PORT = 6667
PASS = f.readline()
NICK = f.readline()
#TODO: Make a master file that takes name a runs a new instance of the bot

try:
    CHANNEL = sys.argv[1]
except:
    raise Exception("No stream input")

global readbuffer
readbuffer = ""

global username
username = ':\w+!'
global said
said = "PRIVMSG\s#.+:.+"

global s

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
        except socket.timeout as e:
            connect()
        except Exception as e:
            print "-Error: " + str(e)
            raise
        temp = str.split(readbuffer, "\n")
        last = temp.pop()
        #print last
        #print temp
        readbuffer = last


        for line in temp:
            reg = re.search(username, line)
            #print 'original match ' + line
            if reg != None:
                name = reg.group()
                #print 'matching ' + line
                regchat = re.search(said, line)#said.match(line)
                if regchat != None:
                    chat = regchat.group()
                    chatLine = str.split(chat, ':')
                    print name[1:-1] + ': ' + chatLine[1]
                else:#should be random housekeeping messages, people arriving and leaving channel, etc.
                    #print name[1:-1] +' talked'
                    pass

connect()
run()
