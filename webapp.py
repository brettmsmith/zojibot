#TODO: Add error catching
from flask import Flask, request, redirect, url_for, render_template, session
from flask.ext.sqlalchemy import SQLAlchemy
from subprocess import Popen, PIPE
import re, requests, os, subprocess, signal

global userToken, CLIENTID, CLIENTSECRET, botProcess
CLIENTID = os.environ["CLIENTID"]
CLIENTSECRET = os.environ["CLIENTSECRET"]
SECRET_KEY = os.environ["SECRET_KEY"]

userToken = None
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]#'postgresql://localhost/test.db'
db = SQLAlchemy(app)
botProcess = None
redirect_uri = 'http://zojibot.herokuapp.com/login'


class User(db.Model):
    id = db.Column(db.Integer, unique = True)
    username = db.Column(db.String(80), primary_key = True)
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

    def editCommand(newResponse):
        self.response = newResponse

    def __init__(self, username, comm, response):
        self.username = username
        self.comm = comm
        self.response = response

    def __repr__(self):
        return 'Username: %s Command: %s Response: %s Command ID: %s' % (self.username, self.comm, self.response, self.id)

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

#HomePage
@app.route('/')
def index():
    if 'username' in session:
        return redirect('/dashboard/')
    #return 'Index page<br><a href="/login">Login here</a>'
    return render_template('index.html')

#ErrorPage
@app.route('/error/')
def error():
    return 'Got an error'

#LoginPage
@app.route('/login/') #use redirect() to redirect user TODO: might want to move the userCode part to a /callback/ page
def login():#TODO: add some try/catches around file stuff and curl stuff
    global userToken, CLIENTID, CLIENTSECRET
    userCode = request.args.get('code')
    print 'userCode: '+str(userCode)
    if userCode != None: #got redirect from twitch
        print 'In /login with userCode'
        urlParams = {'client_id':CLIENTID, 'client_secret':CLIENTSECRET, 'grant_type':'authorization_code', 'redirect_uri':redirect_uri, 'code':str(userCode)}
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
                    name = User.query.get(username)
                    print 'Found name ' + str(name)+ ' in database'
                    if name == None:
                        print 'Name was none'
                        print 'Adding new user ' + username + ' to database'
                        newUser = User(username)
                        db.session.add(newUser)
                        db.session.commit()
                except Exception as e:
                    print 'Exception: '+str(e)
                    print 'Adding new user ' + username + ' to database'
                    newUser = User(username)
                    db.session.add(newUser)
                    db.session.commit()
                print 'Sessioning username: '+username

                try:
                    session['username'] = username
                except Exception as e:
                    print 'Error: '+str(e)
                    return redirect('/error/')
                print 'Redirecting to profile'
                return redirect('/dashboard/')
            else:#error
                print 'Error: username not parsed'
        else:#error getting token
            print 'Error: Token not received'
    else: #need to inform&redirect user to twitch or check for cookie&send to user
        #redirect
        redirectURL = r'https://api.twitch.tv/kraken/oauth2/authorize?response_type=code&client_id='+CLIENTID+r'&redirect_uri='+redirect_uri#&scope=[space separated list of scopes]
        print "Printing for posterity:\nClientid: "+CLIENTID+"\nURL: "+redirectURL
        return redirect(redirectURL)

#StartBotPage
@app.route('/start/')
def startbot():
    global botProcess

    if 'username' in session:
        username = session['username']
        if botProcess == None:
            print 'STARTING BOT'
            botProcess = subprocess.Popen('python bot.py '+username, shell=True, preexec_fn=os.setsid).pid
    return redirect('/dashboard/')

#StopBotPage
@app.route('/stop/')
def stopbot():
    global botProcess

    if 'username' in session:
        if botProcess != None:
            try:
                print 'STOPPING BOT'
                #botProcess.kill()
                os.killpg(botProcess, signal.SIGTERM)
                botProcess = None
            except Exception as e:
                return 'Error: '+str(e)
    return redirect('/dashboard/')

#DashboardPage
@app.route('/dashboard/')#TODO: add command editing and saving, then restart bot
def profile():
    global botProcess

        #TODO: Add in database stuff
    if 'username' in session:
        username = session['username']
        #check request to start bot
        #result = 'Hello, ' + username + '<br> <a href="/edit/">Edit</a><br> Add new command: <br><form action="/add/"> Command: <input type="text" name="command"><br>Response:<input type="text" name="response"><br><input type="submit" value="Submit"></form>'
        action = ''
        value = ''
        text = ''
        status = ''
        if botProcess == None: #TODO: Do a checkup on bot status (maybe later w/ javascript?)
            #button = 'Bot status: Stopped<br><form action="/start/"> <button type="submit" name="bot" value="start">Start bot</button></form>'
            status = 'Stopped'
            action = '"/start/"'
            value = "start"
            text = "Start bot"
        else:
            #button = 'Bot status: Started<br><form action="/stop/"> <button type="submit" name="bot" value="stop">Stop bot</button></form>'
            status = 'Running'
            action = '"/stop/"'
            value = "stop"
            text = "Stop bot"
        #return result+'<br><a href="/logout/">Logout</a>'
        return render_template('dashboard.html', username=username, action=action, value=value, text=text, status=status)

    else: #no username in session
        return render_template('login_redirect.html')


#AddCommandPage
@app.route('/add/')
def addCommand():

    if 'username' in session:
        username = session['username']
        command = request.args.get('command')
        response = request.args.get('response')
        print 'Adding command: '+command
        if command != '!edit':
            newCommand = Command(username, command, response)
            db.session.add(newCommand)
            db.session.commit()
        return redirect('/dashboard/')

    else: #no username in session
        return render_template('login_redirect.html')

#EditCommandsPage
@app.route('/edit/')
def editCommands():
    #TODO: Sessioning, check for token
    if 'username' in session:
        username = session['username']
        query = User.query.filter_by(username=username)
        if query != None:
            commands = Command.query.filter_by(username=username)
            result = 'Commands:<br>'
            if commands != None:
                count = 0
                for c in commands:
                    count += 1
                    result = result + repr(c) + '<br>'
                if count == 0:
                    result = result + 'None'
            result += '<br><a href="/dashboard">Home</a>'
            return result
        else:#user not found
            pass #should be redirect to login screen
    else: #no username in session
        return render_template('login_redirect.html')

#LogoutPage
@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect('/')

#if __name__ == '__main__':
def run():
    #app.debug = True
    db.create_all()
    #db.drop_all()
    app.secret_key = SECRET_KEY
    #app.run()

run()

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
