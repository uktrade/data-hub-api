# flake8: noqa

from gevent import monkey; monkey.patch_all()
from psycogreen.gevent import patch_psycopg; patch_psycopg()
from elasticapm.instrumentation.control import instrument; instrument()  # noqa: E402,E702

import os
import signal

import gevent
from gevent.pywsgi import WSGIServer
from django.core.wsgi import get_wsgi_application

server = WSGIServer(('0.0.0.0', int(os.environ.get('PORT', '8000'))), get_wsgi_application())
gevent.signal_handler(signal.SIGTERM, server.stop)

server.serve_forever()
gevent.get_hub().join()
