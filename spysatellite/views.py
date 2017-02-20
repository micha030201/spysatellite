import re

from flask import redirect, url_for, render_template, request, abort

from spysatellite import app
from spysatellite.twitter import scrape


optimal = re.compile('^[a-z0-9_-]+$')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_string = request.form['input_string']
        input_string = input_string.lower().strip().replace(' ', '_')
        if not optimal.match(input_string[1:]):
            abort(400)
        
        control_symbol = input_string[0]
        if control_symbol == '#':
            return redirect(url_for('twitter_hashtag',
                                    hashtag=input_string[1:]))
        elif control_symbol == '@':
            return redirect(url_for('twitter_user', user=input_string[1:]))
        else:
            return redirect(url_for('twitter_search', search=input_string))
    return render_template('twitter.html')

@app.route('/twitter')
def twitter_searchbar():
    return redirect(url_for('index'))


@app.route('/twitter/user/<user>')
def twitter_user(user):
    if not optimal.match(user):
        abort(400)
    twitter_path = user
    title = '@' + user
    twitter_icon = url_for('static', filename='twitter_icon.png')
    return scrape(twitter_path, title=title, icon=twitter_icon)
    
@app.route('/twitter/user/<user>/with_replies')
def twitter_user_replies(user):
    if not optimal.match(user):
        abort(400)
    twitter_path = user + '/with_replies'
    title = '@{} (w/ replies)'.format(user)
    twitter_icon = url_for('static', filename='twitter_icon.png')
    return scrape(twitter_path, title=title, icon=twitter_icon)

@app.route('/twitter/hashtag/<hashtag>')
def twitter_hashtag(hashtag):
    if not optimal.match(hashtag):
        abort(400)
    twitter_path = 'hashtag/{}?f=tweets'.format(hashtag)
    title = '#' + hashtag
    twitter_icon = url_for('static', filename='twitter_icon.png')
    return scrape(twitter_path, title=title, icon=twitter_icon)

@app.route('/twitter/search/<search>')
def twitter_search(search):
    if not optimal.match(search):
        abort(400)
    twitter_path = 'search?f=tweets&q=' + search
    title = '🔎' + search.replace('_', ' ')
    twitter_icon = url_for('static', filename='twitter_icon.png')
    return scrape(twitter_path, title=title, icon=twitter_icon)



