import logging.config

from flask import Flask
app = Flask(__name__, instance_relative_config=True)
app.config.from_object('spysatellite.default_settings')
app.config.from_pyfile('spysatellite.cfg', silent=True)

if not app.config['UNSHORTEN_URLS']:
    # So that we don't end up with broken frames
    app.config['MAKE_IFRAMES'] = False


if app.config['ENABLE_LOGGING']:
    app.logger  # Create the logger. Does not work without this line.
    logging.config.dictConfig(app.config['LOGGING_CONFIG'])


import spysatellite.views
