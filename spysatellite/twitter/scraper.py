import logging
from datetime import datetime
from random import randint

import requests
from bs4 import BeautifulSoup
from werkzeug.utils import escape
from werkzeug.contrib.atom import AtomFeed, FeedEntry
from flask import request

from spysatellite import app, HEADERS


def remove_spaces(string):
    return ' '.join(string.split())

def get_fullpath(path):
    path = remove_spaces(path).strip()
    path = path.strip('/')
    return 'https://twitter.com/' + path

# Yes, it is easier than getting the href attribute
def get_handle_fullpath(handle):
    return get_fullpath(handle.replace('@', ''))

def get_hashtag_fullpath(hashtag):
    hashtag = hashtag.replace('?src=hash', '').replace('#', '')
    hashtag = 'hashtag/{}?f=tweets'.format(hashtag)
    return get_fullpath(hashtag)


def make_link(url, text=None):
    text = text or url
    return '<a href="{}" rel="noreferrer" target="_blank">{}</a>'.format(url, text)

def make_image(url):
    return '<br /><img src="{}" />'.format(url)

def make_quote(text, author_name, author_handle):
    return '''
        <p><strong>{}</strong> {}:</p>
        <blockquote><p>{}</p></blockquote>
    '''.format(author_name,
               make_link(get_handle_fullpath(author_handle),
                         text=author_handle.strip()),
               text)

def make_not_supported():
    return '''
        <br /><br />
        <i>This media type is not supported :(
        <br />
        Here, have a cat gif instead:</i>
    ''' + make_image(
        'http://thecatapi.com/api/images/get?format=src&type=gif&nvm=' +
        str(randint(0, 999))
    )


class Ignore(Exception):
    pass

def parse_text_content(node):
    for subnode in node.children:
        if subnode.name == None:  # Just strings
            yield escape(subnode).replace('\n', '<br />')
        elif 'u-hidden' in subnode['class']:  # Stuff we don't care about
            continue
        elif subnode.name == 'strong':  # Because it's a thing apparently
            yield escape(subnode.string)
        elif subnode.name == 'img':  # Emoji
            yield subnode['alt']
        elif 'twitter-hashflag-container' in subnode['class']:
            # Hashtags with emoji, because life is never easy
            yield make_link(
                get_hashtag_fullpath(subnode.a.text),
                # The emoji is not actually a part of hashtag though
                text=subnode.a.text
            )
        elif (subnode.name in ('a', 'span') and
              'twitter-hashtag' in subnode['class']):
            yield make_link(
                get_hashtag_fullpath(subnode.text),
                text=subnode.text
            )
        elif (subnode.name in ('a', 'span') and
              'twitter-atreply' in subnode['class']):
            yield make_link(
                get_handle_fullpath(subnode.text),
                text=subnode.text
            )
        elif subnode.name in ('a', 'span'):
            yield make_link(subnode['data-expanded-url'])

def parse_media_content(branch):
    for node in branch.select('.AdaptiveMedia-photoContainer'):
        yield make_image(node['data-image-url'])
    if branch.select_one('.PlayableMedia'):
        yield make_not_supported()

def parse_quote_content(branch):
    def content():
        yield from parse_text_content(
            branch.select_one('.QuoteTweet-text')
        )
        if branch.select_one('.QuoteMedia-photoContainer'):
            yield make_image(
                branch.select_one(
                    '.QuoteMedia-photoContainer'
                )['data-image-url']
            )
        elif branch.select_one('.QuoteMedia-videoPreview'):
            yield make_not_supported()
    yield make_quote(
        ''.join(content()),
        # replace is there for &nbsp; spaces in emoji pictures
        branch.select_one('.QuoteTweet-fullname').text.replace('\xa0', ''),
        branch.select_one('.QuoteTweet-screenname').text
    )

def parse_full_tweet_content(branch):
    yield from parse_text_content(branch.select_one('p.TweetTextSize'))
    if branch.select_one('.QuoteTweet'):
        yield from parse_quote_content(
            branch.select_one('.QuoteTweet .tweet-content')
        )
    elif branch.select_one('.AdaptiveMedia'):
        yield from parse_media_content(
            branch.select_one('.AdaptiveMedia')
        )
    elif branch.select_one('.card2'):
        yield make_not_supported()

def parse_tweet_element(branch):
    branch = branch.div
    if 'user-pinned' in branch['class']:  # no support for :not()
        raise Ignore()
    
    if branch.get('data-retweeter'):
        tweet_type = 'Retweet'
    elif branch.get('data-is-reply-to'):
        tweet_type = 'Reply'
    else:
        tweet_type = 'Tweet'
    
    tweet_link = get_fullpath(branch['data-permalink-path'])
    
    author_nick = branch['data-screen-name']
    author_name = branch['data-name']
    author = author_name + ' @' + author_nick
    
    time_posted = datetime.fromtimestamp(int(
        branch.select_one('span._timestamp')['data-time']
    ))
    
    tweet_content = ''.join(parse_full_tweet_content(
        branch.select_one('.content')
    ))
    
    return FeedEntry(
        title=tweet_type,
        content=tweet_content,
        content_type='html',
        author=author,
        url=tweet_link,
        id=tweet_link,
        updated=time_posted,
        published=time_posted
    )

def scrape(twitter_path, title='twitter feed'):
    r = requests.get(get_fullpath(twitter_path),
                     headers=HEADERS, timeout=5)
    if r.status_code == 404:
        return 'Twitter returned 404: Not Found. Check your spelling.', 424    
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'lxml')
    
    feed = AtomFeed(
        title=title,
        feed_url=request.url,
        url=request.host_url,
        subtitle=soup.select_one('meta[name=description]')['content'],
        icon='https://abs.twimg.com/favicons/favicon.ico',
    )
    
    for node in soup.select('#stream-items-id > [id|=stream-item-tweet]'):
        try:
            feed.add(parse_tweet_element(node))
        except Ignore:  # I hope 'Ignore' is self-explanatory
            continue 
        except:
            app.logger.error('\n\n' + node.prettify())
            raise
    
    return feed

