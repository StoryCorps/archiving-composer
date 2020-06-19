#flaskapp.wsgi
import sys
sys.path.insert(0, '/var/www/html/flaskapp')

from audiocomposer import app as application

