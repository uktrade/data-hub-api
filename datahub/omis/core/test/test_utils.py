from unittest import mock
import pytest

from datahub.omis.core.utils import generate_reference


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
