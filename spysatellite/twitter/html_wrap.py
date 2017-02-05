from random import randint

from spysatellite.twitter.functions import get_handle_fullpath

def link(url, text=None):
    text = text or url
    return '<a href="{}" rel="noreferrer" target="_blank">{}</a>'.format(url, text)

def image(url):
    return '<br /><img src="{}" />'.format(url)
    

def quote(text, author_name, author_handle):
    return '''
        <p><strong>{}</strong> {}:</p>
        <blockquote><p>{}</p></blockquote>
    '''.format(author_name,
               link(get_handle_fullpath(author_handle),
                    text=author_handle.strip()),
               text)

def not_supported():
    return '''
        <br /><br />
        <i>This media type is not supported :(
        <br />
        Here, have a cat gif instead:</i>
    ''' + image(
        'http://thecatapi.com/api/images/get?format=src&type=gif&nvm=' +
        str(randint(0, 999))
    )


