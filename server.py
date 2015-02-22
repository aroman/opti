import os
import json
import flask
import httplib2
import rethinkdb as r
import rethinkdb.errors
from functools import wraps
from pprint import pprint as pp

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client import client

app = flask.Flask(__name__)
app.debug = True
app.secret_key = 'SUPER FUCKIN SECRET'

DB_HOST = "db.opti.work"
CLIENT_ID = "614450015763-gudcs7evjopheo8h6nb9q9ct6ga42pqj.apps.googleusercontent.com"

@app.before_request
def setup_db():
    try:
        flask.g.db_conn = r.connect(host=DB_HOST)
    except rethinkdb.errors.RqlDriverError:
        abort(503, "Couldn't connect to rethinkdb :(")

@app.before_request
def hydrate_credentials():
    if 'credentials' not in flask.session: return
    s = json.loads(flask.session.get('credentials'))
    credential = client.OAuth2Credentials(s['access_token'], s['client_id'],
       s['client_secret'], s['refresh_token'], s['token_expiry'],
       s['token_uri'], s['user_agent'],
       revoke_uri=s['revoke_uri'],
       id_token=s['id_token'],
       token_response=s['token_response'])
    http = httplib2.Http()
    http = credential.authorize(http)
    flask.g.service = build("calendar", "v3", http=http)

@app.teardown_request
def teardown_request(exception):
    try:
        flask.g.db_conn.close()
    except AttributeError:
        pass

def authorized(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in flask.session:
            return redirect(url_for('/', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# @app.route("/test", methods=['GET'])
# def get_todos():
#     selection = list(r.table('test').run(flask.g.db_conn))
#     return json.dumps(selection)

@app.route('/')
def index():
    if 'credentials' in flask.session:
        return flask.redirect("/app")
    return flask.render_template('index.html')

@app.route('/app')
@authorized
def app_():
    # yyyy-mm-ddTHH:MM:ss
    body = {
      "timeMin": "2015-02-22T00:00:00Z",
      "timeMax": "2015-02-23T00:00:00Z",
      "id": "aviromanoff@gmail.com"
    }
    fb = flask.g.service.freebusy().query(body=body).execute()
    # {'kind': 'calendar#freeBusy',
    #  'timeMax': '2015-02-23T00:00:00.000Z',
    #  'timeMin': '2015-02-22T00:00:00.000Z'}
    pp(fb)
    return flask.render_template('app.html')

@app.route('/get-results', methods=["POST"])
@authorized
def get_results():
    # 1. get everyone's schedules
    # 2. get list of start and end times for each user's schedule
    # 3. convert start and end times (google -> algorithm)
    # 4. turn #3 into a dictionary and give it to algorithm function
    # 5. algorithm -> user format
    # 6. return #5 to client 
    print flask.g.credentials
    if 'credentials' not in flask.session:
        return flask.redirect("/")
    return flask.render_template('app.html')

@app.route('/schedule-meeting', methods=["POST"])
@authorized
def schedule_meeting():
    # 1. convert to google format
    # 2. create the events for all the users
    # 3. send an email
    if 'credentials' not in flask.session:
        return flask.redirect("/")
    return flask.render_template('app.html')

@app.route('/store-token', methods=["POST"])
def store_token():
    code = flask.request.data
    try:
       # Upgrade the authorization code into a credentials object
       oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
       oauth_flow.redirect_uri = 'postmessage'
       credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
       response = flask.make_response(
           json.dumps('Failed to upgrade the authorization code.'), 401)
       response.headers['Content-Type'] = 'application/json'
       return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
      response = flask.make_response(json.dumps(result.get('error')), 500)
      response.headers['Content-Type'] = 'application/json'
      return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
      response = flask.make_response(
          json.dumps("Token's client ID does not match app's."), 401)
      response.headers['Content-Type'] = 'application/json'
      return response
    stored_credentials = flask.session.get('credentials')
    if stored_credentials is not None:
      response = flask.make_response(json.dumps('Current user is already connected.'),
                               200)
      response.headers['Content-Type'] = 'application/json'
      return response
    # Store the access token in the flask.session for later use.
    flask.session['credentials'] = credentials.to_json()
    response = flask.make_response(json.dumps('Successfully connected user.', 200))
    return response

@app.route('/signout')
def signout():
    return "not implemented yet"

if __name__ == '__main__':
    app.run()
