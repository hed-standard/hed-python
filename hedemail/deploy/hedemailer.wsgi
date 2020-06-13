#!/usr/bin/python
import sys
activate_this = '/var/www/gollum/env/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))
sys.path.insert(0, "/var/www/gollum/hedemailer")
from hedemailer.create_app import app as application
