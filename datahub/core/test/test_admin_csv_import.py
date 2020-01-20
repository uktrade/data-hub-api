from codecs import BOM_UTF8
from os.path import splitext

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from datahub.core.admin_csv_import import BaseCSVImportForm


class ExampleCSVImportForm(BaseCSVImportForm):
    """Subclass of BaseCSVImportForm to use in tests."""

    required_columns = {'data'}
    csv_file_field_label = 'Data'


class TestBaseCSVImportForm:
    """Tests BaseCSVImportForm."""

    def test_csv_file_field_label_is_set(self):
        """Test that the label of the csv_file field is correctly set."""
        form = ExampleCSVImportForm()
        assert form.fields['csv_file'].label == form.csv_file_field_label

    @pytest.mark.parametrize('encoding', ('windows-1252', 'utf-8', 'utf-8-sig'))
    def test_valid_file_is_loaded(self, encoding):
        """Test that the form validates with a valid file and reads its data."""
        csv_contents = """data\r
row1à\r
row2é\r
"""
        file = SimpleUploadedFile('test.csv', csv_contents.encode(encoding))
        form = ExampleCSVImportForm(
            {},
            {'csv_file': file},
        )

        assert form.is_valid()
        with form.open_file_as_dict_reader() as dict_reader:
            assert list(dict_reader) == [
                {'data': 'row1à'},
                {'data': 'row2é'},
            ]

    @pytest.mark.parametrize('filename', ('noext', 'file.blah', 'test.test', 'test.csv.docx'))
    def test_does_not_allow_invalid_file_extensions(self, filename):
        """Test that the form rejects various invalid file extensions."""
        file = SimpleUploadedFile(filename, b'test')
        form = ExampleCSVImportForm(
            {},
            {'csv_file': file},
        )

        _, ext = splitext(filename)

        assert 'csv_file' in form.errors
        assert form.errors['csv_file'] == [
            f'File extension “{ext[1:]}” is not allowed. Allowed extensions are: csv.',
        ]

    def test_does_not_allow_file_without_required_column(self):
        """Test that the form rejects a CSV file that doesn't contain a 'data' column."""
        file = SimpleUploadedFile('test.csv', b'test\r\nrow')
        form = ExampleCSVImportForm(
            {},
            {'csv_file': file},
        )

        assert 'csv_file' in form.errors
        assert form.errors['csv_file'] == [
            'This file is missing the following required columns: data.',
        ]

    @pytest.mark.parametrize(
        'file_contents',
        (
            b'test\xc3\x28\r\nrow',
            b"""email\r
test1@datahub\r
\xc3\x28
""",
        ),
    )
    def test_does_not_allow_files_with_invalid_utf8(self, file_contents):
        """Test that the form rejects a CSV file with invalid UTF-8."""
        file = SimpleUploadedFile('test.csv', BOM_UTF8 + file_contents)
        form = ExampleCSVImportForm(
            {},
            {'csv_file': file},
        )

        assert 'csv_file' in form.errors
        assert form.errors['csv_file'] == ['There was an error decoding the file contents.']
