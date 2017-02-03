from flask import redirect, url_for

from spysatellite import app

@app.route('/')
def index():
    return redirect(url_for('twitter_searchbar'))
