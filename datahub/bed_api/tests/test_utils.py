from datahub.bed_api.utils import remove_blank_from_dict


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
