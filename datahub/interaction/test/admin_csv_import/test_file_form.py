import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.core.exceptions import DataHubException
from datahub.interaction.admin_csv_import.file_form import InteractionCSVForm
from datahub.interaction.test.admin_csv_import.utils import (
    make_csv_file_from_dicts,
    make_matched_rows,
    make_multiple_matches_rows,
    make_unmatched_rows,
)


@pytest.mark.django_db
class TestInteractionCSVForm:
    """Tests for InteractionCSVForm."""

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
