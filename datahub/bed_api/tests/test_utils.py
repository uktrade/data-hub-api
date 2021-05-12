import os
from collections import OrderedDict

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
