import os
import json
import flask
import httplib2
import rethinkdb as r
import rethinkdb.errors

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = flask.Flask(__name__)
app.debug = True
app.secret_key = 'SUPER FUCKIN SECRET'

DB_HOST = "db.opti.work"
CLIENT_ID = "614450015763-gudcs7evjopheo8h6nb9q9ct6ga42pqj.apps.googleusercontent.com"

@app.before_request
def before_request():
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

@app.route("/test", methods=['GET'])
def get_todos():
    selection = list(r.table('test').run(flask.g.db_conn))
    return json.dumps(selection)

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/app')
def app_():
    print flask.session
    return flask.render_template('app.html')

@app.route('/store-token', methods=["POST"])
def store_token():
    code = flask.request.data
    gplus_id = flask.request.args.get("gplus_id")
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
    # Verify that the access token is used for the intended user.
    # if result['user_id'] != gplus_id:
    #   response = flask.make_response(
    #       json.dumps("Token's user ID doesn't match given user ID."), 401)
    #   response.headers['Content-Type'] = 'application/json'
    #   return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
      response = flask.make_response(
          json.dumps("Token's client ID does not match app's."), 401)
      response.headers['Content-Type'] = 'application/json'
      return response
    stored_credentials = flask.session.get('credentials')
    stored_gplus_id = flask.session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
      response = flask.make_response(json.dumps('Current user is already connected.'),
                               200)
      response.headers['Content-Type'] = 'application/json'
      return response
    # Store the access token in the flask.session for later use.
    flask.session['credentials'] = credentials.to_json()
    flask.session['gplus_id'] = gplus_id
    response = flask.make_response(json.dumps('Successfully connected user.', 200))
    return response

@app.route('/signout')
def signout():
    return "not implemented yet"

if __name__ == '__main__':
    app.run()
