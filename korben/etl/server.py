import functools
import decimal, datetime
import json

import flask
import sqlalchemy as sqla

from korben import db
from . import extract, transform

CONNECTION = None
METADATA = None

app = flask.Flask(__name__)  # NOQA


def handle_data_float(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)

@app.route('/', methods=['POST'])
def root():
    retval = {}
    for entity_name, guids in flask.request.json.items():
        result = extract.from_cdms_psql(METADATA, entity_name, guids)
        transform_func = functools.partial(
            transform.from_cdms_psql, METADATA, entity_name
        )
        retval[entity_name] = list(map(transform_func, result))
    return json.dumps(retval, default=handle_data_float)

def main():
    global CONNECTION
    CONNECTION = db.poll_for_engine().connect()
    global METADATA
    METADATA = sqla.MetaData(bind=CONNECTION)
    METADATA.reflect()
    app.run('0.0.0.0', '8080')
