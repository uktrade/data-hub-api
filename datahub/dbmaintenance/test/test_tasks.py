from itertools import chain
from unittest.mock import MagicMock, Mock

import pytest

from datahub.core.test.support.factories import ForeignAndM2MModelFactory, MetadataModelFactory
from datahub.core.test.support.models import NullableWithDefaultModel
from datahub.dbmaintenance.tasks import (
    copy_foreign_key_to_m2m_field,
    replace_null_with_default,
)


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
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 3),
            (10, 5, 3),
            (11, 6, 2),
            (11, 12, 1),
            (0, 5, 1),
        ),
    )
    def test_replaces_null_with_given_default(
            self,
            monkeypatch,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that null values are replaced with the default value explicitly specified."""
        replace_null_with_default_mock = Mock(
            side_effect=replace_null_with_default,
            wraps=replace_null_with_default,
        )
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.replace_null_with_default',
            replace_null_with_default_mock,
        )

        objs = (
            [NullableWithDefaultModel(nullable_without_default=None)] * num_objects
            + [NullableWithDefaultModel(nullable_without_default=False)] * 10
        )
        NullableWithDefaultModel.objects.bulk_create(objs)

        replace_null_with_default_mock.apply_async(
            args=('support.NullableWithDefaultModel', 'nullable_without_default'),
            kwargs={'default': True, 'batch_size': batch_size},
        )

        assert replace_null_with_default_mock.apply_async.call_count == expected_batches
        assert NullableWithDefaultModel.objects.filter(
            nullable_without_default__isnull=True,
        ).count() == 0
        assert NullableWithDefaultModel.objects.filter(
            nullable_without_default=False,
        ).count() == 10

    @pytest.mark.parametrize(
        'field,default,expected_error_msg',
        (
            (
                'nullable_without_default',
                None,
                'nullable_without_default does not have a non-null default value',
            ),
            (
                'nullable_with_callable_default',
                None,
                'callable defaults for nullable_with_callable_default are not supported',
            ),
            (
                'non_nullable_with_default',
                None,
                'non_nullable_with_default is not nullable',
            ),
            (
                'non_nullable_with_default',
                True,
                'non_nullable_with_default is not nullable',
            ),
        ),
    )
    def test_raises_error_on_invalid_field(self, monkeypatch, field, default, expected_error_msg):
        """
        Test that an error is raised if the task is called with:
         - a model field without a default
         - a model field with a callable default
         - a non-nullable field
         - a non-nullable field and an explicit default
        """
        res = replace_null_with_default.apply_async(
            args=('support.NullableWithDefaultModel', field),
            kwargs={'default': default},
        )
        with pytest.raises(ValueError) as excinfo:
            assert res.get()
        assert str(excinfo.value) == expected_error_msg


@pytest.mark.django_db
class TestCopyForeignKeyToM2MField:
    """Tests for the copy_foreign_key_to_m2m_field task."""

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
    def test_successfully_copies_data(
            self,
            monkeypatch,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that the task copies data for various batch sizes."""
        copy_foreign_key_to_m2m_field_mock = Mock(wraps=copy_foreign_key_to_m2m_field)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.copy_foreign_key_to_m2m_field',
            copy_foreign_key_to_m2m_field_mock,
        )

        objects_to_update = ForeignAndM2MModelFactory.create_batch(num_objects, values=[])
        objects_already_with_m2m_values = ForeignAndM2MModelFactory.create_batch(
            5,
            values=[MetadataModelFactory()],
        )
        objects_with_null_value = ForeignAndM2MModelFactory.create_batch(10, value=None)

        result = copy_foreign_key_to_m2m_field_mock.apply_async(
            args=('support.ForeignAndM2MModel', 'value', 'values'),
            kwargs={'batch_size': batch_size},
        )

        assert result.successful()
        assert copy_foreign_key_to_m2m_field_mock.apply_async.call_count == expected_batches

        for obj in chain(
            objects_to_update,
            objects_already_with_m2m_values,
            objects_with_null_value,
        ):
            obj.refresh_from_db()

        # List comprehensions (rather than generator expressions) used in the all() calls to give
        # more useful information in assertion failures
        # These objects should have been updated by the task
        assert all([list(obj.values.all()) == [obj.value] for obj in objects_to_update])
        # These objects should not have been modified
        assert all(
            [
                obj.values.filter(pk=obj.value.pk).count() == 0
                for obj in objects_already_with_m2m_values
            ],
        )
        # These objects should not have been modified
        assert all([obj.values.count() == 0 for obj in objects_with_null_value])

    def test_rolls_back_on_error(self, monkeypatch):
        """Test that the task rolld back when an error is raised."""
        copy_foreign_key_to_m2m_field_mock = Mock(wraps=copy_foreign_key_to_m2m_field)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.copy_foreign_key_to_m2m_field',
            copy_foreign_key_to_m2m_field_mock,
        )

        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.logger.info',
            Mock(side_effect=ValueError),
        )

        num_objects = 10
        objects_to_update = ForeignAndM2MModelFactory.create_batch(num_objects, values=[])

        result = copy_foreign_key_to_m2m_field_mock.apply_async(
            args=('support.ForeignAndM2MModel', 'value', 'values'),
            kwargs={'batch_size': num_objects},
        )

        with pytest.raises(ValueError):
            result.get()

        assert copy_foreign_key_to_m2m_field_mock.apply_async.call_count == 1

        for obj in objects_to_update:
            obj.refresh_from_db()

        # List comprehensions (rather than generator expressions) used in the all() calls to give
        # more useful information in assertion failures
        # These objects should not have been modified due to the roll back
        assert all([obj.values.count() == 0 for obj in objects_to_update])

    def test_aborts_when_already_in_progress(self, monkeypatch):
        """Test that the task aborts when a task for the same field is already in progress."""
        copy_foreign_key_to_m2m_field_mock = Mock(wraps=copy_foreign_key_to_m2m_field)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.copy_foreign_key_to_m2m_field',
            copy_foreign_key_to_m2m_field_mock,
        )

        # Have to mock rather than acquire the lock as locks are per connection (if the lock is
        # already held by the current connection, the current connection can still acquire it
        # again).
        advisory_lock_mock = MagicMock()
        advisory_lock_mock.return_value.__enter__.return_value = False
        monkeypatch.setattr('datahub.dbmaintenance.tasks.advisory_lock', advisory_lock_mock)
        copy_foreign_key_to_m2m_field_mock.apply(args=('label', 'old-field', 'new-field'))

        # The task should not have been scheduled again as the task should've exited instead
        copy_foreign_key_to_m2m_field_mock.apply_async.assert_not_called()
