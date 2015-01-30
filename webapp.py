from flask import Flask
from flask import request
import subprocess
import tempfile
import re

global userToken
userToken = None
app = Flask(__name__)

def parseCurlForUsername(f):#strip the username out of the json response
    match = re.search("\"user_name\":\s\"(\w+)\",", f.read())
    if match != None:
        return match[14:-1]
    else:
        return None

@app.route('/')
def index():
    return 'Index page'

@app.route('/login/') #use redirect() to redirect user
def login(userCode = None):
    global userToken
    if userCode != None: #got redirect from twitch
        #TODO:POST https://api.twitch.tv/kraken/oauth2/token client_id=[your client ID]
            '''&client_secret=[your client secret]
            &grant_type=authorization_code
            &redirect_uri=[your registered redirect URI]
            &code=[code received from redirect URI]'''
        subprocess.call('curl')
        userToken = userCode
        #TODO: get username from twitch and redirect to /user/username
        stdOut = tempfile.TemporaryFile()
        subprocess.call("curl -H 'Accept: application/vnd.twitchtv.v2+json' -H 'Authorization: OAuth <access_token>' -X GET https://api.twitch.tv/kraken", stdout=stdOut)
        username = parseCurlForUsername(stdOut)
        if username != None:
            redirect(url_for('/user/'+username))
        else:#error
            pass
    else: #need to inform&redirect user to twitch or check for cookie&send to user
        pass

@app.route('/user/<username>/')
def profile(username=None):
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
