from datetime import datetime

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory
from datahub.dnb_match.test.factories import DnBMatchingCSVRecord

pytestmark = pytest.mark.django_db


FROZEN_TIME = datetime(2018, 6, 1, 2, tzinfo=utc)


class TestDnbMatchingCSVRecord:
    """Tests for the DnbMatchingCSVRecord model."""

    def test_record_can_be_created(self):
        """Test that DnbMatchingCSVRecord record can be created."""
        record = DnBMatchingCSVRecord()
        assert record

    def test_cannot_save_model_without_valid_match_candidates(self):
        """Test that a model without valid match candidates cannot be saved."""
        with pytest.raises(ValueError) as excinfo:
            DnBMatchingCSVRecord(data={'what is this': 'value'})

        assert str(excinfo.value) == 'The data must be a list of match candidates.'

    def test_cannot_save_model_with_unexpected_fields_for_match_candidates(self):
        """
        Test that a model cannot be saved if it contains unexpected fields for match candidates.
        """
        with pytest.raises(ValueError) as excinfo:
            DnBMatchingCSVRecord(data=[{'what is this': 'value'}])

        assert str(excinfo.value) == 'The data match candidates contain unexpected fields.'

    def test_cannot_save_model_if_select_duns_number_that_does_not_exist_in_data(self):
        """
        Test that a model cannot be saved if selected duns_number doesn't exist in the data.
        """
        record = DnBMatchingCSVRecord()
        record.selected_duns_number = '12345'
        with pytest.raises(ValueError) as excinfo:
            record.save()

        assert str(excinfo.value) == 'Selected duns_number does not exist in the data.'

    def test_can_save_match_candidates(self):
        """Test that a model with valid match candidates can be saved."""
        record = DnBMatchingCSVRecord()
        record.data = _get_match_candidates()
        record.save()

        record.refresh_from_db()
        assert record.data == _get_match_candidates()

    @freeze_time(FROZEN_TIME)
    def test_can_select_a_match_candidate(self):
        """Test that a model with selected match candidate can be saved."""
        record = DnBMatchingCSVRecord(data=_get_match_candidates())
        adviser = AdviserFactory()
        record.select_match_candidate(adviser, 12345)
        record.save()

        record.refresh_from_db()
        assert record.selected_duns_number == str(12345)
        assert record.selected_by == adviser
        assert record.selected_on == FROZEN_TIME
        assert record.no_match_reason is None
        assert record.no_match_description is None

    @freeze_time(FROZEN_TIME)
    def test_can_provide_a_reason_of_no_match_candidate(self):
        """Test that a model with selected match candidate can be saved."""
        record = DnBMatchingCSVRecord(data=_get_match_candidates())
        adviser = AdviserFactory()
        record.select_match_candidate(adviser, None, 'I do not know', 'Cats know')
        record.save()

        record.refresh_from_db()
        assert record.selected_duns_number is None
        assert record.selected_by == adviser
        assert record.selected_on == FROZEN_TIME
        assert record.no_match_reason == 'I do not know'
        assert record.no_match_description == 'Cats know'


def _get_match_candidates():
    return [
        {
            'duns_number': 12345,
            'name': 'test name',
            'global_ultimate_duns_number': 12345,
            'global_ultimate_name': 'test name global',
            'global_ultimate_country': 'USA',
            'address_1': '1st LTD street',
            'address_2': '',
            'address_town': 'London',
            'address_postcode': 'SW1A 1AA',
            'address_country': {
                'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                'name': 'United States',
            },
            'confidence': 10,
            'source': 'cats',
        },
        {
            'duns_number': 12346,
            'name': 'test name',
            'global_ultimate_duns_number': 12345,
            'global_ultimate_name': 'test name global',
            'global_ultimate_country': 'USA',
            'address_1': '1st LTD street',
            'address_2': '',
            'address_town': 'London',
            'address_postcode': 'SW1A 1AA',
            'address_country': {
                'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                'name': 'United States',
            },
            'confidence': 10,
            'source': 'cats',
        },
    ]
