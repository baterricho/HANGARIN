import os
import sys

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# PYTHONANYWHERE WSGI CONFIGURATION
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Path to your project directory. 
# Based on your setup, it looks like your code is in a nested folder:
path = '/home/richo/HANGARIN/HANGARIN'

if path not in sys.path:
    sys.path.append(path)

# Set the settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# Initialize the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
