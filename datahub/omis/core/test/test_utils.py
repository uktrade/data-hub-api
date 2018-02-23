from unittest import mock

import pytest
from freezegun import freeze_time

from datahub.omis.core.utils import generate_datetime_based_reference, generate_reference


class TestGenerateReference:
    """Tests for the generate_reference utility function."""

    def test_defaults(self):
        """
        Test that it returns the value from its `gen` if the value
        hasn't been used before.
        """
        model = mock.Mock()
        model.objects.filter().exists.return_value = False

        reference = generate_reference(model, lambda: 'something')
        assert reference == 'something'

    def test_with_prefix(self):
        """
        Test that if a prefix is specified, it will be used to generate the reference.
        """
        model = mock.Mock()
        model.objects.filter().exists.return_value = False

        reference = generate_reference(model, lambda: 'something', prefix='pref/')
        assert reference == 'pref/something'

    def test_with_collision(self):
        """
        Test that if gen returns a collision, the next available generated value
        is used instead.
        """
        model = mock.Mock()
        model.objects.filter().exists.side_effect = [True, False]
        gen = mock.Mock()
        gen.side_effect = ['1st try', '2nd try']

        reference = generate_reference(model, gen)
        assert reference == '2nd try'

    def test_max_retries_reached(self):
        """
        Test that if there are n max collisions, the function raises RuntimeError.
        """
        model = mock.Mock()
        model.objects.filter().exists.side_effect = [True] * 10

        with pytest.raises(RuntimeError):
            generate_reference(model, lambda: 'something')


class TestGenerateDateTimeBasedReference:
    """Tests for the generate_datetime_based_reference utility function."""

    @freeze_time('2017-04-18 13:00:00')
    def test_defaults(self):
        """Test the value with default params."""
        model = mock.Mock()
        model.objects.select_for_update().filter.return_value = []
        model.objects.filter().exists.return_value = False

        reference = generate_datetime_based_reference(model)
        assert reference == '201704180001'

    @freeze_time('2017-04-18 13:00:00')
    def test_with_prefix(self):
        """
        Test that if a prefix is specified, it will be used to generate the reference.
        """
        model = mock.Mock()
        model.objects.select_for_update().filter.return_value = []
        model.objects.filter().exists.return_value = False

        reference = generate_datetime_based_reference(model, prefix='pref/')
        assert reference == 'pref/201704180001'

    @freeze_time('2017-04-18 13:00:00')
    def test_with_collision(self):
        """
        Test that if there's already a record with that reference, the seq part is incremented.
        """
        model = mock.Mock()
        model.objects.select_for_update().filter.return_value = []
        model.objects.filter().exists.side_effect = [True, False]

        reference = generate_datetime_based_reference(model)
        assert reference == '201704180002'

    @freeze_time('2017-04-18 13:00:00')
    def test_non_first_record_of_day(self):
        """
        Test that if there are already some record for that day,
        the seq part starts counting from the next number.
        """
        model = mock.Mock()
        model.objects.select_for_update().filter.return_value = [mock.Mock(), mock.Mock()]
        model.objects.filter().exists.return_value = False

        reference = generate_datetime_based_reference(model)
        assert reference == '201704180003'

    def test_max_retries_reached(self):
        """
        Test that if there are n max collisions, the function raises RuntimeError.
        """
        model = mock.Mock()
        model.objects.select_for_update().filter.return_value = []
        model.objects.filter().exists.side_effect = [True] * 10

        with pytest.raises(RuntimeError):
            generate_datetime_based_reference(model)
