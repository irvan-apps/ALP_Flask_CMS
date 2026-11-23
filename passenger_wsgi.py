import sys
import os

# Tambahkan direktori root aplikasi ke dalam path Python
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import Flask instance dengan nama 'application' (standar WSGI Passenger di DirectAdmin/cPanel)
from app import app as application
