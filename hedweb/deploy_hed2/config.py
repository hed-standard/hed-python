"""
This module contains the configurations for the HEDTools application.
"""

import os
import tempfile


class Config(object):
    LOG_DIRECTORY = '/var/log/hedtools'
    LOG_FILE = os.path.join(LOG_DIRECTORY, 'error.log')
    if not os.path.exists('/var/log/hedtools/tmp.txt'):
        f = open('/var/log/hedtools/tmp.txt', 'w+')
        f.write(str(os.urandom(24)))
        f.close()
    f = open('/var/log/hedtools/tmp.txt', 'r')
    SECRET_KEY = f.read()  # os.getenv('SECRET_KEY') # os.urandom(24)
    f.close()
    STATIC_URL_PATH = None
    STATIC_URL_PATH_ATTRIBUTE_NAME = 'STATIC_URL_PATH'
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'hedtools_uploads')
    URL_PREFIX = None
    HED_CACHE_FOLDER = '/var/cache/hed_cache'

class DevelopmentConfig(Config):
    DEBUG = False
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    URL_PREFIX = '/hed'
    STATIC_URL_PATH = '/hed/static'


class TestConfig(Config):
    DEBUG = False
    TESTING = True


class DebugConfig(Config):
    DEBUG = True
    TESTING = False
