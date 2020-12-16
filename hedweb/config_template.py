"""
This module contains the default configurations for hedwebmap
"""

import os
import tempfile


class Config(object):
    LOG_DIRECTORY = '/var/log/hedtools3'
    LOG_FILE = os.path.join(LOG_DIRECTORY, 'error.log')
    if not os.path.exists('/var/log/hedtools3/tmp.txt'):
        f = open('/var/log/hedtools3/tmp.txt', 'w+')
        f.write(str(os.urandom(24)))
        f.close()
    f = open('/var/log/hedtools3/tmp.txt', 'r')
    SECRET_KEY = f.read()  # os.getenv('SECRET_KEY') # os.urandom(24)
    f.close()
    STATIC_URL_PATH = None
    STATIC_URL_PATH_ATTRIBUTE_NAME = 'STATIC_URL_PATH'
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'hedtools3_uploads')
    URL_PREFIX = None
    HED_CACHE_FOLDER = None


class DevelopmentConfig(Config):
    DEBUG = False
    TESTING = False

class TestConfig(Config):
    DEBUG = False
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class DebugConfig(Config):
    DEBUG = True
    TESTING = False
