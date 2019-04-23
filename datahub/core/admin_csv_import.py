import csv
import io

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
        encoding = detection_result['encoding']

        # Check that the file can actually be decoded using the detected encoding so that
        # we don't need to worry about encoding errors when reading the CSV
        file_field.seek(0)
        self._validate_encoding(file_field, encoding)

        file_field.seek(0)
        csv_reader = csv.DictReader(io.TextIOWrapper(file_field, encoding=encoding))

        # Check that the CSV file has the required column
        self._validate_columns(csv_reader)

        return csv_reader

    @classmethod
    def _validate_encoding(cls, file_field, encoding):
        try:
            stream = io.TextIOWrapper(file_field, encoding=encoding)
            for _ in stream:
                pass

            # Detach the file from TextIOWrapper; this stops it being automatically closed
            stream.detach()
        except UnicodeError as exc:
            raise ValidationError(
                cls.UNICODE_DECODE_ERROR_MESSAGE,
                code='unicode-decode-error',
            ) from exc

    @classmethod
    def _validate_columns(cls, csv_reader):
        missing_columns = sorted(cls.required_columns - set(csv_reader.fieldnames))

        if missing_columns:
            msg = cls.MISSING_COLUMNS_MESSAGE.format(
                missing_columns=', '.join(missing_columns),
            )

            raise ValidationError(msg, code='missing-columns')
