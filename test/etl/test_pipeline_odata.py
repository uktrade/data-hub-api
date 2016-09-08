'''
Test the ETL pipeline and polling sync against an OData test service. It runs
in a slightly simpler container environment (since custom Postgres compilation
isn’t required here). It basically does this:
    - Overwrite transformation mapping (since this test doesn’t run against the
      full CDMS schema)
    - Make a request to `$metadata` to get OData metadata XML (see conftest.py
      in this directory)
    - Translate the metadata XML to SQL `CREATE` statements
    - Run these statements against the `test_odata` database
    - Make changes in the OData service through the API
    - Check these updates are caught by the polling sync and that an ETL run is
      gtriggered
    - Verify that `test_odata` and `test` databases are in the expected state
'''
from korben.odata_psql import odata_sql_schema
from korben.odata_psql import separate_constraints

TEST_MAPPINGS = {
    'Products': {
        'to': 'products',
        'local': (
            ('ID', 'id'),
            ('ReleaseDate', 'release_date'),
            ('Rating', 'rating'),
            ('Price', 'price'),
        ),
        'foreign': (
            '''
            
            '''
            (('ID', 'id'), 'notes'),
        ),
    },
    'Categories': {
        'to': 'categories',
        'local': (
            ('ID', 'id'),
            ('Name', 'name'),
        )
    },
    'Suppliers': {
        'to': 'suppliers',
    }
}


def test_pipeline(odata_test_service, tmpfile, db_connection):
    client = odata_test_service
    resp = client.make_request('get', client.CDMS_REST_BASE_URL + '$metadata')
    metadata = tmpfile()
    with open(metadata.name, 'wb') as metadata_fh:
        metadata_fh.write(resp.content)
    sql_file = tmpfile()
    sql = odata_sql_schema(metadata.name)
    with open(sql_file.name, 'wb') as sql_fh:
        sql_fh.write(sql)
    create_sql, _ = separate_constraints(sql_file.name)
    db_connection.execute(create_sql)
    import ipdb;ipdb.set_trace()
