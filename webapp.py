#TODO: Add error catching
from flask import Flask
from flask import request
import subprocess
import tempfile
import re

fs = open('appauth.dat')
global userToken, CLIENTID, CLIENTSECRET
CLIENTID = fs.readline()
CLIENTSECRET = fs.readline()
userToken = None
app = Flask(__name__)
fs.close()

def parseCurlForUsername(f):#strip the username out of the json response
    match = re.search("\"user_name\":\s\"(\w+)\",", f.read())
    if match != None:
        return match[14:-1]
    else:
        return None

def parseCurlForAuthToken(f):#get client token from json response
    match = re.search("\"access_token\":\s\"(.*?)\",") #might have to change to specificify alphanumeric
    if match != None:
        return match[19:-2]
    else:
        return None

@app.route('/')
def index():
    return 'Index page'

@app.route('/login/') #use redirect() to redirect user TODO: might want to move the userCode part to a /callback/ page
def login(userCode = None):#TODO: add some try/catches around file stuff and curl stuff
    global userToken, CLIENTID, CLIENTSECRET
    if userCode != None: #got redirect from twitch
        stdOut = tempfile.TemporaryFile()
        curlCall = "curl -H https://api.twitch.tv/kraken/oauth2/token client_id="+CLIENTID+"&client_secret="+CLIENTSECRET+"&grant_type=authorization_code&redirect_uri=http://localhost:5000/login&code="+userCode
        subprocess.call(curlCall, stdout = stdOut)
        userToken = parseCurlForAuthToken(stdOut)
        stdOut.close()
        if userToken != None:
            #TODO: get username from twitch and redirect to /user/username
            stdOut = tempfile.TemporaryFile()
            curlCall = "curl -H 'Accept: application/vnd.twitchtv.v2+json' -H 'Authorization: OAuth "+userToken+"' -X GET https://api.twitch.tv/kraken"
            subprocess.call(curlCall, stdout=stdOut)
            username = parseCurlForUsername(stdOut)
            if username != None:
                redirect(url_for('/user/'+username))
            else:#error
                pass
        else:#error getting token
            pass
    else: #need to inform&redirect user to twitch or check for cookie&send to user
        pass
        #redirect
        redirectURL = 'https://api.twitch.tv/kraken/oauth2/authorize?response_type=code&client_id='+CLIENTID+'&redirect_uri=+http://localhost:5000/login'#&scope=[space separated list of scopes]
        redirect(redirectURL)

@app.route('/user/<username>/')
def profile(username=None):
    if username != None:
        return 'Success, '+username
    else:#error
        return 'Please <a href="/login">Login</a>'
    #check for token
    #check for config file for user? if none, make one

if __name__ == '__main__':
    app.debug = True
    app.run()

'''
    ok so go to index, there's a bit of info about the bot and a login button
    at the top.

    Login page redirects to the twitch account login (might want a buffer page
    explaining they're going to be redirected and what the login is for)

    User logs in on twitch, gets redirected to a temp page where to get the username
    and make a page for the user (way to check if they already have a page, or will flask
    know that the page already exists and it's safe to call url_for() anyways?)
        TODO: figure out how to use tokens and stuff so people don't have to login
        each time. Also needs to be secure

    User home page might eventually have statistics or something, but the main event
    will be adding/editing commands that the bot can do.
        TODO: Flesh out bot functionality on spam, and make an easy way for users to add
        commands (don't make them do any regex) (list of banned users?)
'''
