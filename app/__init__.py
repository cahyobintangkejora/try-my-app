from flask import Flask
from itsdangerous.serializer import Serializer
from itsdangerous.url_safe import URLSafeSerializer
import logging
from . import config

# instantiate itsdangerous
serializer = Serializer(config.SECRET_KEY, signer_kwargs={'sep': '$.$'})
us_serializer = URLSafeSerializer(config.SECRET_KEY, signer_kwargs={'sep': '$.$'})

# konfigurasi logger biar nggak berisik
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# instantiate flask
app = Flask(__name__)
app.config.from_pyfile('config.py')

# import view function / controller / route
from app.controller.dashboard import d_dashboard
from app.controller.kelola import d_kelola
