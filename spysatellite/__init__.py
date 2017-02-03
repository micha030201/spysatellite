import logging

from flask import Flask
app = Flask(__name__)


file_handler = logging.FileHandler('spysatellite.log')
#file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(filename)s: %(levelname)s: %(message)s'
))

app.logger.addHandler(file_handler)
#app.logger.setLevel(logging.DEBUG)


HEADERS = {
    'Accept-Language': 'en,en-US', 
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                   AppleWebKit/537.36 (KHTML, like Gecko) \
                   Chrome/55.0.2883.87 Safari/537.36', 
}


import spysatellite.views
import spysatellite.twitter.views
