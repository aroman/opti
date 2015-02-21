import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<img style="width:250px" src="http://www.clker.com/cliparts/r/o/x/t/p/y/purple-postit-hi.png">'
