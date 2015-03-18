#TODO: Add error catching
from flask import Flask, request, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from subprocess import Popen, PIPE
import re, requests, os

fs = open('appauth.dat')
global userToken, CLIENTID, CLIENTSECRET
CLIENTID = str.rstrip(fs.readline())
CLIENTSECRET = str.rstrip(fs.readline())
fs.close()
userToken = None
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]#'postgresql://localhost/test.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True)
    #commandSet = db.Column(db.String(5000), unique = False)
    commandSet = db.relationship('Command', backref='commands')


    def __init__(self, username):
        self.username = username
        #self.commandSet = 'None'

    def __repr__(self):
        return '<User %r>' % self.username

class Command(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'))
    comm = db.Column(db.String(1000), unique=True)
    response = db.Column(db.String(1000), unique=False)

    def __init__(self, username, comm, response):
        self.username = username
        self.comm = comm
        self.response = response

    def __repr__(self):
        return 'Username: %s Command %s Response: %s' % (self.username, self.comm, self.response)

def parseCurlForUsername(f):#strip the username out of the json response
    match = re.search("\"user_name\":\s*\"(\w+)\"", f)
    if match != None:
        return str(match.group(1))
    else:
        print 'Returning username as None'
        return None

def parseCurlForAuthToken(f):#get client token from json response
    print 'Searching through: ' + f
    match = re.search("\"access_token\":\s*\"(.*?)\",", f) #might have to change to specificify alphanumeric
    if match != None:
        return str(match.group(1))
    else:
        print 'Returning auth token as None'
        return None

def getUserCommands(user, s):#TODO: Need to find a way to parse, someone could type anything as a command
    #Basic delimiter will just be '|'
    if s != 'None':
        pass
    else:#No commands
        return None

def setUserCommands(user, s):
    pass

@app.route('/dbtest/')
def dbtest():
    return '<form action="/dbtest/results">User:<br><input type="text" name="username"><br>Command:<br><input type="text" name="command"><br><input type="submit" value="submit"></form>'

@app.route('/dbtest/reset/')
def reset():
    db.drop_all()
    return 'Success'

@app.route('/dbtest/results/')
def dbresults():
    user = request.args.get('username')
    command = request.args.get('command')
    print 'User: %s' %user
    client = User(user)
    com = Command(user, command)
    #db.session.add(client)
    db.session.add(com)
    db.session.commit()
    try:
        query = Command.query.filter_by(username=user).filter_by(comm=command).first_or_404()
    except Exception as e:
        print 'Error: %d-%s' % (e.errno, e.strerror)
    return 'Hello %s. Your command was: %s' % (query.username, query.comm)

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
        urlParams = {'client_id':CLIENTID, 'client_secret':CLIENTSECRET, 'grant_type':'authorization_code', 'redirect_uri':'http://localhost:5000/login', 'code':str(userCode)}
        r = requests.post('https://api.twitch.tv/kraken/oauth2/token', params = urlParams)
        print 'Parsing response: '+r.text
        userToken = parseCurlForAuthToken(r.text)
        if userToken != None:
            print 'Got user token back it\'s '+userToken
            headers = {'Accept':'application/vnd.twitchtv.v2+json', 'Authorization': 'OAuth '+userToken}
            rq = requests.get('https://api.twitch.tv/kraken', headers = headers)
            print 'Getting username from ' + rq.text
            username = parseCurlForUsername(rq.text)
            print 'Got username back, it\'s '+username
            if username != None:
                try:
                    name = User.query.get(username=username)
                except:
                    print 'Added new user ' + username + ' to database'
                    newUser = User(username)
                    db.session.add(newUser)
                    db.session.commit()
                return redirect(url_for('profile',username=username))
            else:#error
                print 'Error: username not parsed'
        else:#error getting token
            print 'Error: Token not received'
    else: #need to inform&redirect user to twitch or check for cookie&send to user
        #redirect

        redirectURL = r'https://api.twitch.tv/kraken/oauth2/authorize?response_type=code&client_id='+CLIENTID+r'&redirect_uri=http://localhost:5000/login'#&scope=[space separated list of scopes]
        print "Printing for posterity:\nClientid: "+CLIENTID+"\nURL: "+redirectURL
        return redirect(redirectURL)

@app.route('/user/<username>/')#TODO: add command editing and saving, then restart bot
def profile(username=None):
    if username != None:
        #TODO: Add in database stuff
        return 'Hello, ' + username + '<br> <a href="/user/' + username + '/edit">Edit</a><br> Add new command: <br><form action="/user/'+username+'/add"> Command: <input type="text" name="command"><br>Response:<input type="text" name="response"><br><input type="submit" value="Submit"></form>'
    else:#error
        return 'Please <a href="/login">Login</a>'
    #check for token
    #check for config file for user? if none, make one
@app.route('/user/<username>/add')
def addCommand(username=None):
    if username != None:
        command = request.args.get('command')
        response = request.args.get('response')
        newCommand = Command(username, command, response)
        db.session.add(newCommand)
        db.session.commit()
        return redirect('/user/'+username+'/')
    else:
        pass
@app.route('/user/<username>/edit/')
def editCommands(username=None):
    if username != None:
        #TODO: Sessioning, check for token
        query = User.query.filter_by(username=username)
        if query != None:
            commands = Command.query.filter_by(username=username)
            result = 'Commands<br>'
            if commands != None:
                for c in commands:
                    result = result + repr(c) + '<br>'
            return result
        else:#user not found
            pass #should be redirect to login screen

if __name__ == '__main__':
    app.debug = True
    db.create_all()
    #db.drop_all()
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
