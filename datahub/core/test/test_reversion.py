from unittest import mock

import pytest

from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS, register_base_model


class TestRegisterBaseModel:
    """Tests for the `register_base_model` decorator."""

    @mock.patch('datahub.core.reversion.reversion')
    def test_without_args(self, mocked_reversion):
        """Test that the default exclude is used if no argument is passed in."""
        register_base_model()
        assert mocked_reversion.register.call_args_list == [
            mock.call(exclude=EXCLUDED_BASE_MODEL_FIELDS),
        ]

    @mock.patch('datahub.core.reversion.reversion')
    def test_with_extra_exclude(self, mocked_reversion):
        """Test that if extra_exclude is passed in, it is appended to the default exclude list."""
        register_base_model(extra_exclude=('other',))
        assert mocked_reversion.register.call_args_list == [
            mock.call(exclude=(*EXCLUDED_BASE_MODEL_FIELDS, 'other')),
        ]

    @mock.patch('datahub.core.reversion.reversion')
    def test_with_explicit_exclude(self, mocked_reversion):
        """Test that if exclude is passed in, it overrides the default one."""
        register_base_model(exclude=('other',))
        assert mocked_reversion.register.call_args_list == [
            mock.call(exclude=('other',)),
        ]

    @mock.patch('datahub.core.reversion.reversion')
    def test_fails_with_extra_exclude_and_exclude(self, mocked_reversion):
        """Test that extra_exclude and exclude cannot be passed in at the same time."""
        with pytest.raises(AssertionError):
            register_base_model(exclude=('other',), extra_exclude=('other',))

    @mock.patch('datahub.core.reversion.reversion')
    def test_with_other_args(self, mocked_reversion):
        """Test passing any other argument forwards it untouched."""
        register_base_model(ignore_duplicates=False)
        assert mocked_reversion.register.call_args_list == [
            mock.call(
                exclude=EXCLUDED_BASE_MODEL_FIELDS,
                ignore_duplicates=False,
            ),
        ]
