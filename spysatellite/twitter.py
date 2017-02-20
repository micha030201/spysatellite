import logging
import traceback
from datetime import datetime
from multiprocessing.dummy import Pool

import requests
from bs4 import BeautifulSoup
from werkzeug.utils import escape
from werkzeug.contrib.atom import AtomFeed, FeedEntry
from flask import request

from spysatellite import app


def get_fullpath(path):
    path = path.strip().strip('/')
    return 'https://twitter.com/' + path

def unshorten_url(url):
    if not app.config['UNSHORTEN_URLS']:
        return url
    return requests.get(
        url,
        allow_redirects=False,
        timeout=1,
        # We would get 200 + js/http-equiv with browser User-Agent
        headers={'User-Agent': ''}
    ).headers['location']

# Yes, it is easier than getting the href attribute
def get_handle_fullpath(handle):
    return get_fullpath(handle.replace('@', ''))

def get_hashtag_fullpath(hashtag):
    hashtag = hashtag.replace('#', '')
    hashtag = 'hashtag/{}?f=tweets'.format(hashtag)
    return get_fullpath(hashtag)


def make_link(url, text=None):
    text = text or url
    return ('<a href="{}" rel="noopener noreferrer"'
            ' target="_blank">{}</a>').format(url, text)

def make_image(url):
    return '<br /><img src="{}" />'.format(url)

def make_youtube_iframe(url):
    if not app.config['MAKE_IFRAMES']:
        return '<br />' + make_link(url)
    
    is_ssl = 1 if 'https://' in url else 0
    if 'youtu.be/' in url:
        video_id = url[16 + is_ssl:]
    elif 'youtube.com/' in url:
        video_id = url[31 + is_ssl:].replace('&', '?')
    else:
        return '<br />' + make_link(url)
    
    url = 'https://www.youtube.com/embed/' + video_id
    return ('<br /><iframe width="560" height="315" src="{}"'
            ' frameborder="0" allowfullscreen></iframe>').format(url)

def make_quote(text, author_name, author_handle):
    return ('<p><strong>{}</strong> {}:</p>'
            '<blockquote><p>{}</p></blockquote>').format(
        author_name,
        make_link(
            get_handle_fullpath(author_handle),
            text=author_handle.strip()
        ),
        text
    )

def make_not_supported():
    return '<br /><i>[UNSUPPORTED-MEDIA]</i>'

def make_quote_unavailable():
    return '<blockquote><p><i>[UNAVAILABLE-TWEET]</i></p></blockquote>'


def parse_text_content(node):
    for subnode in node.children:
        if subnode.name == None:  # Just strings
            yield (
                escape(subnode)
#                .strip('\n')  # Happens in quotes for some reason
                # We're gonna hope noone's indenting with single spaces
                .replace('  ', '&nbsp; ')
                .replace('\n', '<br />')
            )
        elif subnode.name == 'strong':  # May not have class
            yield escape(subnode.string)
        elif 'u-hidden' in subnode['class']:  # Stuff we don't care about
            continue
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

def parse_card2_summary(branch):
    return '<br />' + make_link(
        unshorten_url(branch.div['data-card-url'])
    )

def parse_card2_player(branch):
    return make_youtube_iframe(
        unshorten_url(branch.div['data-card-url'])
    )

def parse_full_tweet_content(branch):
    yield from parse_text_content(branch.select_one('p.TweetTextSize'))
    if branch.select_one('.QuoteTweet'):
        yield from parse_quote_content(
            branch.select_one('.QuoteTweet .tweet-content')
        )
    elif branch.select_one('.QuoteTweet--unavailable'):
        yield make_quote_unavailable()
    elif branch.select_one('.AdaptiveMedia'):
        yield from parse_media_content(
            branch.select_one('.AdaptiveMedia')
        )
    elif branch.select_one('.card2'):
        branch = branch.select_one('.card2')
        if branch['data-card2-name'] in ('summary', 'summary_large_image'):
            yield parse_card2_summary(branch)
        elif branch['data-card2-name'] == 'player':
            yield parse_card2_player(branch)
        else:
            yield make_not_supported()

def parse_tweet_element(branch):
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
        updated=time_posted,
        published=time_posted
    )

def process_tweet_li(branch):
    branch = branch.div
    if 'user-pinned' in branch['class']:  # no support for :not()
        return
    
    try:
        return parse_tweet_element(branch)
    except:
        app.logger.error('\n' + branch.prettify() + traceback.format_exc())
        return

def scrape(twitter_path, title='twitter feed', icon=''):
    r = requests.get(
        get_fullpath(twitter_path),
        headers={
            'Accept-Language': 'en,en-US',
            'User-Agent': app.config['UA_DESKTOP'],
        },
        timeout=5
    )
    if r.status_code == 404:
        return 'Twitter returned 404: Not Found. Check your spelling.', 424    
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'lxml')
    
    feed = AtomFeed(
        title=title,
        feed_url=request.url,
        url=request.host_url,
        subtitle=soup.select_one('meta[name=description]')['content'],
        icon=icon,
    )
    
    tweet_nodes = soup.select('#stream-items-id > [id|=stream-item-tweet]')
    with Pool(10) as p:
        for entry in p.imap_unordered(process_tweet_li, tweet_nodes):
            if entry is not None:
                feed.add(entry)
    
    return feed

