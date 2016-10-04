import datetime
import decimal
import json

import flask

from .main import from_cdms_psql

app = flask.Flask(__name__)  # NOQA


def handle_date_float(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


@app.route('/cdms', methods=['POST'])
def root():
    retval = {}
    for entity_name, guids in flask.request.json.items():
        retval[entity_name] = from_cdms_psql(entity_name, guids)
    return json.dumps(retval, default=handle_date_float)


def main():
    app.run('0.0.0.0', '8080')
