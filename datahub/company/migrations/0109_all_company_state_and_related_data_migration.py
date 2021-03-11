from os import path
from django.db import connection
from django.db import migrations


def read_relative_file(file_name):
    """
        Read a file in the same directory as the current file
        TODO: Move into some sort of migration util
    """
    file_path = path.join(path.dirname(__file__), file_name)
    print(file_path)
    with open(file_path, 'r') as file:
        result = file.read()
    return result


def execute_sql_command(sql_statement):
    """
        Execute a sql command using the current connection
         TODO: Move into some sort of migration util
    """
    with connection.cursor() as live_connection:
        return live_connection.execute(sql_statement)


def read_and_execute(file_name):
    """
        Reads file in the current test directory and executes the
        sql content
    """
    sql_statement = read_relative_file(file_name)
    return execute_sql_command(sql_statement)


def run_international_area_code_data_migration(app, schema_editor):
    """
        Clean registered postcode address data
    """
    print(app, schema_editor)
    read_and_execute('update_international_area_code.sql')


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0007_administrativearea_area_code')
    ]
    operations = [
        migrations.RunPython(run_international_area_code_data_migration),
    ]
