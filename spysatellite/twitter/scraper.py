from datetime import datetime
import logging

import requests
from bs4 import BeautifulSoup
from werkzeug.contrib.atom import AtomFeed, FeedEntry
from flask import request

from spysatellite import app, HEADERS
from spysatellite.twitter import html_wrap
from spysatellite.twitter.functions import *


class Ignore(Exception):
    pass

def parse_text_content(node):
    output = ''
    for subnode in node.children:
        if subnode.name == None:  # Just strings
            output += subnode.replace('\n', '<br />')
        elif subnode.name == 'strong':  # Because it's a thing apparently
            output += str(subnode.string)
        elif 'u-hidden' in subnode['class']:  # Stuff we don't care about
            continue
        elif subnode.name == 'img':  # Emoji
            output += subnode['alt']
        # Direct tweets:
        elif subnode.name == 'a' and 'twitter-hashtag' in subnode['class']:
            output += html_wrap.link(
                get_hashtag_fullpath(subnode.text),
                text=subnode.text
            )
        elif subnode.name == 'a' and 'twitter-atreply' in subnode['class']:
            output += html_wrap.link(
                get_handle_fullpath(subnode.text),
                text=subnode.text
            )
        elif subnode.name == 'a':
            output += html_wrap.link(subnode['data-expanded-url'])
        elif 'twitter-hashflag-container' in subnode['class']:
            # Hashtags with emoji, because life is never easy
            output += html_wrap.link(
                get_handle_fullpath(subnode.a.text),
                text=subnode.a.text  # The emoji is thrown out, yes
            )
        # Quoted tweets:
        elif subnode.name == 'span' and 'twitter-hashtag' in subnode['class']:
            output += html_wrap.link(
                get_hashtag_fullpath(subnode.text),
                text=subnode.text
            )
        elif subnode.name == 'span' and 'twitter-atreply' in subnode['class']:
            output += html_wrap.link(
                get_handle_fullpath(subnode.text),
                text=subnode.text
            )
        elif subnode.name == 'span':
            output += html_wrap.link(subnode['data-expanded-url'])
    return output

def parse_media_content(branch):  # Operates levels above parse_text
    output = ''
    if branch.select_one('.QuoteTweet'):
        branch = branch.select_one('.QuoteTweet .tweet-content')
        quote_tweet_text = parse_text_content(
            branch.select_one('.QuoteTweet-text')
        )
        if branch.select_one('.QuoteMedia-photoContainer'):
            quote_tweet_text += html_wrap.image(
                branch.select_one(
                    '.QuoteMedia-photoContainer'
                )['data-image-url']
            )
        elif branch.select_one('.QuoteMedia-videoPreview'):
            quote_tweet_text += html_wrap.not_supported()
        output = html_wrap.quote(
            quote_tweet_text,
            branch.select_one('.QuoteTweet-fullname').text,
            branch.select_one('.QuoteTweet-screenname').text
        )
    elif branch.select_one('.AdaptiveMedia'):
        branch = branch.select_one('.AdaptiveMedia')
        for node in branch.select('.AdaptiveMedia-photoContainer'):
            output += html_wrap.image(node['data-image-url'])
        if branch.select_one('.PlayableMedia'):
            output = html_wrap.not_supported()
    elif branch.select_one('.card2'):
        output = html_wrap.not_supported()
    return output

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
    
    #tweet_id = branch['data-tweet-id']
    tweet_link = get_fullpath(branch['data-permalink-path'])
    
    author_nick = branch['data-screen-name']
    author_name = branch['data-name']
    author = author_name + ' @' + author_nick
    
    time_posted = datetime.fromtimestamp(int(
        branch.select_one('span._timestamp')['data-time']
    ))
    
    branch = branch.select_one('.content')
    
    tweet_text = parse_text_content(branch.select_one('p.TweetTextSize'))
    tweet_media = parse_media_content(branch)
    
    tweet_content = remove_spaces(tweet_text + tweet_media)
    
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
    
    feed =  AtomFeed(
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

