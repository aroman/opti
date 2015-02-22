import os
import json
import flask
import pyrfc3339
import httplib2
import rethinkdb as r
import rethinkdb.errors
from functools import wraps
from pprint import pprint as pp
import algorithms, timeConversion

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

def cred_from_cred_id(cred_id):
  cred_from_db = r.table('credentials').get(cred_id).run(flask.g.db_conn)
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
  return credentials

def authorize(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credential_id' not in flask.session:
          return flask.redirect('/')
        credentials = cred_from_cred_id(flask.session.get('credential_id'))
        http = credentials.authorize(httplib2.Http())
        flask.g.calendar = build("calendar", "v3", http=http)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/app')
@authorize
def app_():
    # yyyy-mm-ddTHH:MM:ss
    # fb = flask.g.calendar.freebusy().query(body=body).execute()
    # {'kind': 'calendar#freeBusy',
    #  'timeMax': '2015-02-23T00:00:00.000Z',
    #  'timeMin': '2015-02-22T00:00:00.000Z'}
    # cursor = r.table('credentials').run(flask.g.db_conn)
    # for credential_doc in cursor:
    #   credentials = cred_from_cred_id(credential_doc['id'])
    #   http = credentials.authorize(httplib2.Http())
    #   calendar = build("calendar", "v3", http=http)
      # calendar.freebusy().query(body=body).execute()
      # pp(credential_doc['id'])
      # pp(calendar)
    return flask.render_template('app.html')

@app.route('/results', methods=["POST"])
@authorize
def results():

    data = json.loads(flask.request.data)

    # 1. get everyone's schedules
    # 2. get list of start and end times for each user's schedule
    # 3. convert (google -> algorithm) & reformat to alice format
    cursor = r.table('credentials').run(flask.g.db_conn)
    aliceData = {}
    for credential_doc in cursor:
      credentials = cred_from_cred_id(credential_doc['id'])
      http = credentials.authorize(httplib2.Http())
      calendar = build("calendar", "v3", http=http)
      body = {
        "timeMin": "2015-02-22T00:00:00-05:00",
        "timeMax": "2015-02-23T00:00:00-05:00",
        "items": [{"id": credential_doc['id']}]
      }
      fb = calendar.freebusy().query(body=body).execute()
      fbtimes = fb['calendars'][credential_doc['id']]['busy']
      # {
      #   "avi@romanoff.me": [(st, end), (st, end)]
      # }
      aliceData[credential_doc['id']] = []
      for fbtime in fbtimes:
        aliceData[credential_doc['id']].append((
          timeConversion.jsonToAlgorithm(fbtime['start']),
          timeConversion.jsonToAlgorithm(fbtime['end'])
        ))
    goodTimes = algorithms.coreScheduler(aliceData)
    results = []
    for goodTime in goodTimes:
      block = {
        'time': timeConversion.algorithmTupleToUser(goodTime),
      }
      results.append(block)
    # 4. algorithm -> user format
    # 5. return #4 to client
    return flask.jsonify(results=results)

@app.route('/schedule-meeting', methods=["POST"])
@authorize
def schedule_meeting():
    # 1. convert to google format
    title = "Meeting Name"  # From form
    creator = "cvsinpa@gmail.com" # From session
    date = timeConversion.userDateToJsonDate(userDate)    # From form
    startTime = timeConversion.algorithmToJson(algorithmStart)  # From algorithm
    startDateTime = startDate + "T" + startTime + "-05:00"  # Hardcoded TZ
    endTime = timeConversion.algorithmToJson(algorithmEnd)
    endDateTime = date + "T" + endTime + "-05:00"

    attendees = ["aviromanoff@gmail.com", "rajatm96@gmail.com"]

    # Somehow have to set sendNotifications to true in request
    body = {
      "creator": {
        "id": creator
      },
      "start": {
        "dateTime": startDateTime
      },
     "summary": title,
     "attendees": [
        {
        "email": attendees[0]
        },
        {
        "email": attendees[1]
        }
      ],
        "end": {
        "dateTime": endDateTime
      }
    }

    # 2. create the events for all the users
      # Send request
    # 3. send an email
      # Set sendNotifications = true
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
