import logging.config

from flask import Flask
app = Flask(__name__, instance_relative_config=True)
app.config.from_object('spysatellite.default_settings')
app.config.from_pyfile('spysatellite.cfg', silent=True)

app.logger  # Create the logger. Does not work without this line.
logging.config.dictConfig(app.config['LOGGING_CONFIG'])


import spysatellite.views
