import os
from collections import OrderedDict

from datahub.bed_api.entities import BedEntity
from datahub.bed_api.repositories import ReadRepository, ReadWriteRepository
from datahub.bed_api.utils import remove_blank_from_dict

NOT_BED_INTEGRATION_TEST_READY = (
    'BED_USERNAME' not in os.environ
    or 'BED_USERNAME' in os.environ
    and os.environ['BED_USERNAME'] == 'test-user@digital.trade.gov.uk'
)


class TestRemovingBlanksFromDictShould:
    """Test remove_blank_from_dict"""

    def test_dictionary_lists_of_dictionaries(self):
        """Test lists in lists get removed"""
        expected = dict(
            cars=[
                dict(make='Volvo', model='V50'),
                dict(colour='Blue', make='VW'),
            ],
        )

        test_data = dict(
            cars=[
                dict(
                    make='Volvo',
                    model='V50',
                    colour=None,
                ),
                dict(
                    make='VW',
                    model='',
                    colour='Blue',
                ),
            ],
        )

        assert remove_blank_from_dict(test_data) == expected


def create_success_query_response(salesforce_object, record_id):
    """
    Create a Salesforce query success response
    :param record_id: Record identifier value
    :param salesforce_object: Salesforce object e.g Contact
    :return: Return a structured success query response
    """
    url = f'/services/data/v42.0/sobjects/{salesforce_object}/{record_id}'
    attributes = OrderedDict(
        [
            ('type', 'Contact'),
            ('url', url),
        ],
    )
    success_query_response = OrderedDict(
        [
            ('totalSize', 1),
            ('done', True),
            (
                'records',
                [
                    OrderedDict(
                        [
                            ('attributes', attributes),
                            ('Id', record_id),
                        ],
                    ),
                ],
            ),
        ],
    )
    return success_query_response


def create_fail_query_response():
    """
    Create a Salesforce query failed response
    :return: Return a structured failed query response
    """
    failed_query_response = OrderedDict(
        [
            ('totalSize', 0),
            ('done', True),
        ],
    )
    return failed_query_response


def delete_and_assert_deletion(
    repository: ReadWriteRepository,
    record_id,
):
    """
    Delete generated record from the database
    :param repository: ReadWriteRepository type
    :param record_id: Identifier to delete
    """
    if record_id and repository:
        delete_contact_response = repository.delete(record_id)
        assert delete_contact_response is not None
        assert delete_contact_response == 204
        exists = repository.exists(record_id)
        assert exists is False


def assert_all_data_exists_on_bed(
    bed_entity: BedEntity,
    record_id,
    repository: ReadRepository,
    validate_data=True,
):
    """
    Verifies the get and data posted on Salesforce
    :param bed_entity: Bed entity that can compare the final data on Salesforce
    :param record_id:  Unique identifier or Id record
    :param repository: Salesforce Repository to retrieve data
    :param validate_data: If True checks all the key values otherwise ignores
    Note: this is mostly ignored when Salesforce changes the data order on lists,
    merges other list data or text fields stripping out characters
    """
    exists = repository.exists(record_id)
    assert exists is True
    salesforce_data = repository.get(record_id)
    assert salesforce_data is not None
    if validate_data:
        for key, value in bed_entity.as_values_only_dict().items():
            failure_message = (
                f'Failed property "{key}" with value "{value}"'
                f' not equal to"{salesforce_data[key]}"'
            )
            assert salesforce_data[key] == value, failure_message
