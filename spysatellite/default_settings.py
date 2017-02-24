
UA_DESKTOP = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
              ' AppleWebKit/537.36 (KHTML, like Gecko)'
              ' Chrome/55.0.2883.87 Safari/537.36')

CONFIGURE_LOGGING = True
LOG_FULL_HTML = False
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(filename)s: %(message)s'
        }
    },
    'handlers': {
        'to_file': {
            'level': 'WARNING',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'spysatellite.log'
        }
    },
    'loggers': {
        'spysatellite': {  # app.logger uses module name logger by default
            'handlers': ['to_file'],
            'level': 'WARNING',
            'propagate': False
        }
    }
}

UNSHORTEN_URLS = True
MAKE_IFRAMES = True
