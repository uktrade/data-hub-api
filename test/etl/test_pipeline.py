'A test of the entire ETL pipeline'
from korben.odata_psql import odata_sql_schema
from korben.odata_psql import separate_constraints


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
