import os
import json
import flask
import rethinkdb as r
import rethinkdb.errors

app = flask.Flask(__name__)
app.debug = True

DB_HOST = "db.opti.work"

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
    return flask.render_template('app.html')

@app.route('/signout')
def signout():
    return "not implemented yet"


if __name__ == '__main__':
    app.run()
