import csv
import io
from contextlib import contextmanager

from chardet import UniversalDetector
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy


class BaseCSVImportForm(forms.Form):
    """Form used for loading a CSV file in the admin site."""

    UNICODE_DECODE_ERROR_MESSAGE = gettext_lazy('There was an error decoding the file contents.')
    MISSING_COLUMNS_MESSAGE = gettext_lazy(
        'This file is missing the following required columns: {missing_columns}.',
    )

    csv_file_field_label = 'CSV file'
    csv_file_field_help_text = None
    required_columns = set()

    csv_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=('csv',))],
    )

    def __init__(self, *args, **kwargs):
        """Initialises the form, dynamically setting the label of the csv_file field."""
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].label = self.csv_file_field_label
        self.fields['csv_file'].help_text = self.csv_file_field_help_text

    def clean_csv_file(self):
        """Validates the uploaded CSV file and creates a CSV DictReader from it."""
        # This could be an instance of InMemoryUploadedFile or TemporaryUploadedFile
        # (depending on the file size)
        file_field = self.cleaned_data['csv_file']

        # Guess the file encoding (primarily to check for a UTF-8 BOM)
        encoding_detector = UniversalDetector()
        for chunk in file_field.chunks():
            encoding_detector.feed(chunk)
            if encoding_detector.done:
                break

        detection_result = encoding_detector.close()
        self.cleaned_data['csv_file_encoding'] = detection_result['encoding']

        # Check that the file can actually be decoded using the detected encoding so that
        # we don't need to worry about encoding errors when reading the CSV
        file_field.seek(0)
        self._validate_encoding()

        file_field.seek(0)
        # Check that the CSV file has the required column
        self._validate_columns()

        file_field.seek(0)
        return file_field

    @contextmanager
    def open_file_as_text_stream(self):
        """
        Opens the CSV file in the csv_file field as a text stream.

        Must only be called if is_valid() has returned True.
        """
        encoding = self.cleaned_data['csv_file_encoding']
        csv_file = self.cleaned_data['csv_file']
        csv_file.seek(0)
        stream = io.TextIOWrapper(csv_file, encoding=encoding)

        try:
            yield stream
        finally:
            # Detach the file from TextIOWrapper; this stops it being automatically closed
            stream.detach()

    @contextmanager
    def open_file_as_dict_reader(self):
        """
        Opens the CSV file in the csv_file field as a csv.DictReader.

        Must only be called if is_valid() has returned True.
        """
        with self.open_file_as_text_stream() as stream:
            yield csv.DictReader(stream)

    def _validate_encoding(self):
        try:
            # Read the entire file one line at a time to trigger any decoding errors.
            with self.open_file_as_text_stream() as stream:
                for _ in stream:
                    pass
        except UnicodeError as exc:
            raise ValidationError(
                self.UNICODE_DECODE_ERROR_MESSAGE,
                code='unicode-decode-error',
            ) from exc

    def _validate_columns(self):
        with self.open_file_as_text_stream() as stream:
            csv_reader = csv.DictReader(stream)
            missing_columns = sorted(self.required_columns - set(csv_reader.fieldnames))

        if missing_columns:
            msg = self.MISSING_COLUMNS_MESSAGE.format(
                missing_columns=', '.join(missing_columns),
            )

            raise ValidationError(msg, code='missing-columns')
