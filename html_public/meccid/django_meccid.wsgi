import os
import sys

sys.path.append('/home/meccid/django_projects/')
sys.path.append('/home/meccid/django_projects/meccid/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
