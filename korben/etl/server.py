import functools
import decimal, datetime
import json

import flask
import sqlalchemy as sqla

from korben import db
from . import transform

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
        table = METADATA.tables[entity_name]
        primary_key = next(
            col.name for col in table.primary_key.columns.values()
        )
        select_statement = (
            sqla
            .select([table])
            .where(table.columns[primary_key].in_(guids))
        )
        result = CONNECTION.execute(select_statement).fetchall()
        transform_func = functools.partial(
            transform.to_leeloo, METADATA, entity_name
        )
        retval[entity_name] = list(map(transform_func, map(dict, result)))
    return json.dumps(retval, default=handle_data_float)

CONNECTION = None
METADATA = None

def main():
    global CONNECTION
    CONNECTION = db.poll_for_engine().connect()
    global METADATA
    METADATA = sqla.MetaData(bind=CONNECTION)
    METADATA.reflect()
    app.run('0.0.0.0', '8080')
