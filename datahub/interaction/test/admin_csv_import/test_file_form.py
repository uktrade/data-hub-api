import csv
import gzip
import hashlib
import io

import pytest
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.files.uploadedfile import SimpleUploadedFile
from reversion.models import Revision, Version

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.company.test.factories import AdviserFactory
from datahub.core.exceptions import DataHubException
from datahub.interaction.admin_csv_import import file_form
from datahub.interaction.admin_csv_import.cache_utils import _cache_key_for_token, CacheKeyType
from datahub.interaction.admin_csv_import.file_form import (
    InteractionCSVForm,
    REVISION_COMMENT,
    UnmatchedRowCollector,
)
from datahub.interaction.admin_csv_import.row_form import (
    CSVRowError,
    DUPLICATE_OF_ANOTHER_ROW_MESSAGE,
)
from datahub.interaction.models import Interaction
from datahub.interaction.test.admin_csv_import.utils import (
    make_csv_file_from_dicts,
    make_matched_rows,
    make_multiple_matches_rows,
    make_unmatched_rows,
)


@pytest.mark.django_db
class TestUnmatchedRowCollector:
    """Tests for UnmatchedRowCollector."""

    def test_to_csv(self):
        """Test CSV file generation."""
        collector = UnmatchedRowCollector()
        input_rows = make_unmatched_rows(2)

        for input_row in input_rows:
            collector.append_row(InteractionCSVForm(data=input_row))

        csv_contents = collector.to_raw_csv()
        with io.BytesIO(csv_contents) as stream:
            reader = csv.reader(io.TextIOWrapper(stream, encoding='utf-8-sig'))
            csv_rows = list(reader)

        assert csv_rows == [
            [
                'theme',
                'kind',
                'date',
                'adviser_1',
                'contact_email',
                'service',
                'communication_channel',
            ],
            [
                input_rows[0]['theme'],
                input_rows[0]['kind'],
                input_rows[0]['date'],
                input_rows[0]['adviser_1'],
                input_rows[0]['contact_email'],
                input_rows[0]['service'],
                input_rows[0]['communication_channel'],
            ],
            [
                input_rows[1]['theme'],
                input_rows[1]['kind'],
                input_rows[1]['date'],
                input_rows[1]['adviser_1'],
                input_rows[1]['contact_email'],
                input_rows[1]['service'],
                input_rows[1]['communication_channel'],
            ],
        ]

        # Check that the file re-validates (so it can be re-uploaded)
        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile('test.csv', csv_contents),
            },
        )
        assert form.is_valid()
        assert form.are_all_rows_valid()


@pytest.mark.django_db
class TestInteractionCSVForm:
    """Tests for InteractionCSVForm."""

    def test_get_row_errors_with_duplicate_rows(self):
        """Test that duplicate rows are tracked and errors returned when encountered."""
        matched_rows = make_matched_rows(5)

        file = make_csv_file_from_dicts(
            # Duplicate the first row
            matched_rows[0],
            *matched_rows,
            *make_unmatched_rows(5),
            *make_multiple_matches_rows(5),
        )

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file.getvalue()),
            },
        )

        assert form.is_valid()

        row_errors = list(form.get_row_error_iterator())
        assert row_errors == [
            CSVRowError(1, NON_FIELD_ERRORS, '', DUPLICATE_OF_ANOTHER_ROW_MESSAGE),
        ]

    @pytest.mark.parametrize(
        'num_matching,num_unmatched,num_multiple_matches,max_returned_rows',
        (
            (5, 6, 7, 5),
            (5, 6, 7, 3),
            (5, 6, 7, 10),
            (5, 0, 0, 5),
            (0, 5, 5, 5),
            (0, 0, 5, 5),
        ),
    )
    def test_get_matching_summary(
        self,
        num_matching,
        num_unmatched,
        num_multiple_matches,
        max_returned_rows,
    ):
        """Test get_matching_summary() with various inputs."""
        input_matched_rows = make_matched_rows(num_matching)
        unmatched_rows = make_unmatched_rows(num_unmatched)
        multiple_matches_rows = make_multiple_matches_rows(num_multiple_matches)

        file = make_csv_file_from_dicts(
            *input_matched_rows,
            *unmatched_rows,
            *multiple_matches_rows,
        )

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file.getvalue()),
            },
        )

        assert form.is_valid()

        matching_counts, returned_matched_rows = form.get_matching_summary(max_returned_rows)

        assert matching_counts == {
            ContactMatchingStatus.matched: num_matching,
            ContactMatchingStatus.unmatched: num_unmatched,
            ContactMatchingStatus.multiple_matches: num_multiple_matches,
        }

        expected_num_returned_rows = min(num_matching, max_returned_rows)
        assert len(returned_matched_rows) == expected_num_returned_rows

        # Check the the rows returned are the ones we expect
        expected_contact_emails = [
            row['contact_email'] for row in input_matched_rows[:expected_num_returned_rows]
        ]
        actual_contact_emails = [row['contacts'][0].email for row in returned_matched_rows]
        assert expected_contact_emails == actual_contact_emails

    def test_get_matching_summary_with_invalid_rows(self):
        """
        Test that get_matching_summary() raises an exception if one of the CSV rows fails
        validation.
        """
        file = make_csv_file_from_dicts(
            {
                'theme': 'invalid',
                'kind': 'invalid',
                'date': 'invalid',

                'adviser_1': 'invalid',
                'contact_email': 'invalid',
                'service': 'invalid',
                'communication_channel': 'invalid',
            },
        )

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file.getvalue()),
            },
        )

        assert form.is_valid()

        with pytest.raises(DataHubException):
            form.get_matching_summary(50)

    @pytest.mark.parametrize('num_matching', (5, 10))
    @pytest.mark.parametrize('num_unmatched', (0, 6))
    @pytest.mark.parametrize('num_multiple_matches', (0, 6))
    @pytest.mark.usefixtures('local_memory_cache')
    def test_save_returns_correct_counts(self, num_matching, num_unmatched, num_multiple_matches):
        """Test that save() returns the expected counts for each matching status."""
        matched_rows = make_matched_rows(num_matching)
        unmatched_rows = make_unmatched_rows(num_unmatched)
        multiple_matches_rows = make_multiple_matches_rows(num_multiple_matches)
        user = AdviserFactory(first_name='Admin', last_name='User')

        file = make_csv_file_from_dicts(
            *matched_rows,
            *unmatched_rows,
            *multiple_matches_rows,
        )
        file_contents = file.getvalue()

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file_contents),
            },
        )

        assert form.is_valid()
        matching_counts, _ = form.save(user)

        assert matching_counts == {
            ContactMatchingStatus.matched: num_matching,
            ContactMatchingStatus.unmatched: num_unmatched,
            ContactMatchingStatus.multiple_matches: num_multiple_matches,
        }

    @pytest.mark.parametrize('num_matching', (5, 10))
    @pytest.mark.parametrize('num_unmatched', (0, 6))
    @pytest.mark.parametrize('num_multiple_matches', (0, 6))
    @pytest.mark.usefixtures('local_memory_cache')
    def test_save_returns_unmatched_rows(self, num_matching, num_unmatched, num_multiple_matches):
        """Test that save() returns an UnmatchedRowCollector with the expected rows."""
        matched_rows = make_matched_rows(num_matching)
        unmatched_rows = make_unmatched_rows(num_unmatched)
        multiple_matches_rows = make_multiple_matches_rows(num_multiple_matches)
        user = AdviserFactory(first_name='Admin', last_name='User')

        file = make_csv_file_from_dicts(
            *matched_rows,
            *unmatched_rows,
            *multiple_matches_rows,
        )
        file_contents = file.getvalue()

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file_contents),
            },
        )

        assert form.is_valid()
        _, unmatched_row_collector = form.save(user)

        assert unmatched_row_collector.rows == [
            *unmatched_rows,
            *multiple_matches_rows,
        ]

    @pytest.mark.parametrize('num_matching', (5, 10))
    @pytest.mark.parametrize('num_unmatched', (0, 6))
    @pytest.mark.parametrize('num_multiple_matches', (0, 6))
    def test_save_creates_interactions(self, num_matching, num_unmatched, num_multiple_matches):
        """Test that save() creates interactions."""
        matched_rows = make_matched_rows(num_matching)
        unmatched_rows = make_unmatched_rows(num_unmatched)
        multiple_matches_rows = make_multiple_matches_rows(num_multiple_matches)
        user = AdviserFactory(first_name='Admin', last_name='User')

        file = make_csv_file_from_dicts(
            *matched_rows,
            *unmatched_rows,
            *multiple_matches_rows,
        )
        file_contents = file.getvalue()

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file_contents),
            },
        )

        assert form.is_valid()
        form.save(user)

        created_interactions = list(Interaction.objects.all())
        assert len(created_interactions) == num_matching

        expected_contact_emails = {row['contact_email'] for row in matched_rows}
        actual_contact_emails = {
            interaction.contacts.first().email for interaction in created_interactions
        }
        # Make sure the test was correctly set up with unique contact emails
        assert len(actual_contact_emails) == num_matching
        # Check that the interactions created are the ones we expect
        # Note: the full saving logic for a row is tested in the InteractionCSVRowForm tests
        assert expected_contact_emails == actual_contact_emails

        expected_source = {
            'file': {
                'name': file.name,
                'size': len(file_contents),
                'sha256': hashlib.sha256(file_contents).hexdigest(),
            },
        }
        # `source` has been set (list used rather than a generator for useful failure messages)
        assert all([
            interaction.source == expected_source for interaction in created_interactions
        ])

    def test_save_creates_versions(self):
        """Test that save() creates versions using django-reversion."""
        num_matching = 5
        matched_rows = make_matched_rows(num_matching)
        user = AdviserFactory(first_name='Admin', last_name='User')

        file = make_csv_file_from_dicts(*matched_rows)
        file_contents = file.getvalue()

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file_contents),
            },
        )

        assert form.is_valid()
        form.save(user)

        created_interactions = list(Interaction.objects.all())
        assert len(created_interactions) == num_matching

        # Single revision created
        assert Revision.objects.count() == 1
        assert Revision.objects.first().get_comment() == REVISION_COMMENT

        # Versions were created (list used rather than a generator for useful failure messages)
        assert all([
            Version.objects.get_for_object(interaction).count() == 1
            for interaction in created_interactions
        ])

    def test_save_rolls_back_on_error(self):
        """Test that save() rolls back if one row can't be saved."""
        user = AdviserFactory(first_name='Admin', last_name='User')

        file = make_csv_file_from_dicts(
            *make_matched_rows(5),
            # an invalid row
            {},
        )
        file_contents = file.getvalue()
        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file_contents),
            },
        )

        assert form.is_valid()
        with pytest.raises(DataHubException):
            form.save(user)

        assert not Interaction.objects.count()

    @pytest.mark.usefixtures('local_memory_cache')
    def test_save_to_cache(self, track_return_values):
        """Test that the form data can be saved to the cache."""
        tracker = track_return_values(file_form, 'token_urlsafe')

        file = make_csv_file_from_dicts(
            *make_matched_rows(1),
            filename='cache-test.csv',
        )

        form = InteractionCSVForm(
            files={
                'csv_file': SimpleUploadedFile(file.name, file.getvalue()),
            },
        )

        assert form.is_valid()
        form.save_to_cache()

        assert len(tracker.return_values) == 1
        token = tracker.return_values[0]

        contents_key = _cache_key_for_token(token, CacheKeyType.file_contents)
        name_key = _cache_key_for_token(token, CacheKeyType.file_name)

        file.seek(0)
        assert gzip.decompress(cache.get(contents_key)) == file.read()
        assert cache.get(name_key) == file.name

    @pytest.mark.usefixtures('local_memory_cache')
    def test_from_token_with_valid_token(self):
        """Test that a form can be restored from the cache."""
        token = 'test-token'
        contents_key = _cache_key_for_token(token, CacheKeyType.file_contents)
        name_key = _cache_key_for_token(token, CacheKeyType.file_name)
        file = make_csv_file_from_dicts(
            *make_matched_rows(1),
            filename='cache-test.csv',
        )
        compressed_data = gzip.compress(file.read())

        cache.set(contents_key, compressed_data)
        cache.set(name_key, file.name)

        form = InteractionCSVForm.from_token(token)

        assert form.is_valid()

        file.seek(0)
        assert file.read() == form.cleaned_data['csv_file'].read()
        assert file.name == form.cleaned_data['csv_file'].name

    @pytest.mark.usefixtures('local_memory_cache')
    @pytest.mark.parametrize(
        'cache_data',
        (
            # only the file contents
            {_cache_key_for_token('test-token', CacheKeyType.file_contents): b'data'},
            # only the file name
            {_cache_key_for_token('test-token', CacheKeyType.file_name): 'name'},
            # nothing
            {},
        ),
    )
    def test_from_token_with_invalid_token(self, cache_data):
        """
        Test that from_token() returns None if there is incomplete data for the token in
        the cache.
        """
        cache.set_many(cache_data)
        form = InteractionCSVForm.from_token('test-token')

        assert form is None
