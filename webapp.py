#TODO: Add error catching
from flask import Flask
from flask import request
from flask import redirect
from subprocess import Popen, PIPE
import tempfile
import re
#import str

fs = open('appauth.dat')
global userToken, CLIENTID, CLIENTSECRET
CLIENTID = str.rstrip(fs.readline())
CLIENTSECRET = str.rstrip(fs.readline())
fs.close()
userToken = None
app = Flask(__name__)


def parseCurlForUsername(f):#strip the username out of the json response
    match = re.search("\"user_name\":\s\"(\w+)\",", f)
    if match != None:
        return match[14:-1]
    else:
        return None

def parseCurlForAuthToken(f):#get client token from json response
    print 'Searching through: ' + f
    match = re.search("\"access_token\":\s\"(.*?)\",", f) #might have to change to specificify alphanumeric
    if match != None:
        return match[19:-2]
    else:
        return None

@app.route('/')
def index():
    return 'Index page<br><a href="/login">Login here</a>'

@app.route('/login/') #use redirect() to redirect user TODO: might want to move the userCode part to a /callback/ page
def login():#TODO: add some try/catches around file stuff and curl stuff
    global userToken, CLIENTID, CLIENTSECRET
    userCode = request.args.get('code')
    print 'userCode: '+str(userCode)
    if userCode != None: #got redirect from twitch
        print 'In /login with userCode'
        #stdOut = tempfile.TemporaryFile()
        curlCall = "curl -X POST https://api.twitch.tv/kraken/oauth2/token?client_id="+CLIENTID+"&client_secret="+CLIENTSECRET+"&grant_type=authorization_code&redirect_uri=http://localhost:5000/login&code="+str(userCode)
        print 'curlCall: '+curlCall
        #subprocess.call(curlCall, stdout = stdOut)
        process = Popen(curlCall, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        print 'Parsing output: '+out+' : '+err
        userToken = parseCurlForAuthToken(out)
        #stdOut.close()
        if userToken != None:
            #TODO: get username from twitch and redirect to /user/username
            print 'Got user token back it\'s '+userToken
            #stdOut = tempfile.TemporaryFile()
            curlCall = "curl -X POST 'Accept: application/vnd.twitchtv.v2+json' -H 'Authorization: OAuth "+userToken+"' -X GET https://api.twitch.tv/kraken"
            #subprocess.call(curlCall, stdout=stdOut)
            proc = Popen(curlCall, shell=True, stdout=PIPE, stderr=PIPE)
            stdOut, err = proc.communicate()
            username = parseCurlForUsername(stdOut)
            print 'Got username back, it\'s '+username
            if username != None:
                return redirect(url_for('/user/'+username))
            else:#error
                print 'Error: username not parsed'
        else:#error getting token
            print 'Error: Token not received'
    else: #need to inform&redirect user to twitch or check for cookie&send to user
        #redirect

        redirectURL = r'https://api.twitch.tv/kraken/oauth2/authorize?response_type=code&client_id='+CLIENTID+r'&redirect_uri=http://localhost:5000/login'#&scope=[space separated list of scopes]
        print "Printing for posterity:\nClientid: "+CLIENTID+"\nURL: "+redirectURL
        return redirect(redirectURL)

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
