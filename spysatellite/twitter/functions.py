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
