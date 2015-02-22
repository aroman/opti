import os
import json
import flask
import pyrfc3339
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

@app.before_request
def setup_db():
    try:
        flask.g.db_conn = r.connect(host=DB_HOST)
    except rethinkdb.errors.RqlDriverError:
        abort(503, "Couldn't connect to rethinkdb :(")

@app.teardown_request
def teardown_request(exception):
    try:
        flask.g.db_conn.close()
    except AttributeError:
        pass

def authorized(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credential_id' not in flask.session:
          return flask.redirect('/')
        c_key = flask.session.get('credential_id')
        cred_from_db = r.table('credentials').get(c_key).run(flask.g.db_conn)
        if not cred_from_db:
          return flask.redirect('/')
        credentials = client.OAuth2Credentials(
          cred_from_db['access_token'],
          cred_from_db['client_id'],
          cred_from_db['client_secret'],
          cred_from_db['refresh_token'],
          pyrfc3339.parse(cred_from_db['token_expiry']).replace(tzinfo=None),
          cred_from_db['token_uri'],
          cred_from_db['user_agent'],
          revoke_uri=cred_from_db['revoke_uri'],
          id_token=cred_from_db['id_token'],
          token_response=cred_from_db['token_response']
        )
        http = httplib2.Http()
        http = credentials.authorize(http)
        flask.g.calendar = build("calendar", "v3", http=http)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
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
    fb = flask.g.calendar.freebusy().query(body=body).execute()
    # {'kind': 'calendar#freeBusy',
    #  'timeMax': '2015-02-23T00:00:00.000Z',
    #  'timeMin': '2015-02-22T00:00:00.000Z'}
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
    return flask.render_template('app.html')

@app.route('/schedule-meeting', methods=["POST"])
@authorized
def schedule_meeting():
    # 1. convert to google format
    # 2. create the events for all the users
    # 3. send an email
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
    http = httplib2.Http()
    result = json.loads(http.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
      response = flask.make_response(json.dumps(result.get('error')), 500)
      response.headers['Content-Type'] = 'application/json'
      return response
    if flask.session.get('credential_id') is not None:
      response = flask.make_response(json.dumps('Current user is already connected.'),
                               200)
      response.headers['Content-Type'] = 'application/json'
      return response
    creds = json.loads(credentials.to_json())
    creds["id"] = flask.session['credential_id'] = creds['id_token']['email']
    query_res = r.table('credentials').insert(creds).run(flask.g.db_conn)
    response = flask.make_response(json.dumps('Successfully connected user.', 200))
    return response

if __name__ == '__main__':
    app.run()
