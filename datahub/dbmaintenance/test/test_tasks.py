from unittest.mock import Mock

import pytest

from datahub.core.test.support.models import NullableWithDefaultModel
from datahub.dbmaintenance.tasks import replace_null_with_default


@pytest.mark.django_db
class TestReplaceNullWithDefault:
    """Tests for the replace_null_with_default task."""

    @pytest.mark.parametrize(
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 3),
            (10, 5, 3),
            (11, 6, 2),
            (11, 12, 1),
            (0, 5, 1),
        ),
    )
    def test_replaces_null_with_default(
            self,
            monkeypatch,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that null values are replaced with the default value for the model field."""
        replace_null_with_default_mock = Mock(
            side_effect=replace_null_with_default,
            wraps=replace_null_with_default,
        )
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.replace_null_with_default',
            replace_null_with_default_mock,
        )

        objs = (
            [NullableWithDefaultModel(nullable_with_default=None)] * num_objects
            + [NullableWithDefaultModel(nullable_with_default=False)] * 10
        )
        NullableWithDefaultModel.objects.bulk_create(objs)

        replace_null_with_default_mock.apply_async(
            args=('support.NullableWithDefaultModel', 'nullable_with_default'),
            kwargs={'batch_size': batch_size},
        )

        assert replace_null_with_default_mock.apply_async.call_count == expected_batches
        assert NullableWithDefaultModel.objects.filter(
            nullable_with_default__isnull=True,
        ).count() == 0
        assert NullableWithDefaultModel.objects.filter(nullable_with_default=False).count() == 10

    @pytest.mark.parametrize(
        'field',
        (
            'nullable_without_default',
            'nullable_with_callable_default',
            'non_nullable_with_default',
        ),
    )
    def test_raises_error_on_invalid_field(self, monkeypatch, field):
        """
        Test that an error is raised if:
         - a model field without a default is specified
         - a model field with a callable default is specified
         - a non-nullable model field is specified
        """
        res = replace_null_with_default.apply_async(
            args=('support.NullableWithDefaultModel', field),
        )
        with pytest.raises(ValueError):
            assert res.get()
