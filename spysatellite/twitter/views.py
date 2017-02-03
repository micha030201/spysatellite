from flask import redirect, url_for, render_template, request

from spysatellite import app
from spysatellite.twitter.scraper import scrape


def normalize(input_string):
    return input_string.lower().strip().replace(' ', '_')


@app.route('/twitter/user/<user>')
def twitter_user(user):
    normalized_user = normalize(user)
    if user != normalized_user:
        return redirect(url_for('twitter_user', user=normalized_user))
    twitter_path = user
    title = '@' + user
    return scrape(twitter_path, title=title)
    
@app.route('/twitter/user/<user>/with_replies')
def twitter_user_replies(user):
    normalized_user = normalize(user)
    if user != normalized_user:
        return redirect(url_for('twitter_user', user=normalized_user))
    twitter_path = user + '/with_replies'
    title = '@{} (w/ replies)'.format(user)
    return scrape(twitter_path, title=title)

@app.route('/twitter/hashtag/<hashtag>')
def twitter_hashtag(hashtag):
    normalized_hashtag = normalize(hashtag)
    if hashtag != normalized_hashtag:
        return redirect(url_for('twitter_hashtag', hashtag=normalized_hashtag))
    twitter_path = 'hashtag/{}?f=tweets'.format(hashtag)
    title = '#' + hashtag
    return scrape(twitter_path, title=title)

@app.route('/twitter/search/<search>')
def twitter_search(search):
    normalized_search = normalize(search)
    if search != normalized_search:
        return redirect(url_for('twitter_search', search=normalized_search))
    twitter_path = 'search?f=tweets&q=' + search
    title = '🔎' + search.replace('_', ' ')
    return scrape(twitter_path, title=title)


@app.route('/twitter', methods=['GET', 'POST'])
def twitter_searchbar():
    if request.method == 'POST':
        input_string = request.form['input_string']
        input_string = normalize(input_string)
        control_symbol = input_string[0]
        if control_symbol == '#':
            return redirect(url_for('twitter_hashtag',
                                    hashtag=input_string[1:]))
        elif control_symbol == '@':
            return redirect(url_for('twitter_user', user=input_string[1:]))
        else:
            return redirect(url_for('twitter_search', search=input_string))
    return render_template('twitter.html')

