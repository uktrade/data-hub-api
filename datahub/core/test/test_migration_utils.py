import datetime
from unittest import mock

import factory
import pytest
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.core.serializers import base

from datahub.core.migration_utils import (
    DeleteModelWithMetadata,
    load_yaml_data_in_migration,
)
from datahub.core.test.support.factories import BookFactory, PersonFactory
from datahub.core.test.support.models import Book, Person


pytestmark = pytest.mark.django_db


class TestLoadYamlInMigration:
    """Tests for the load_yaml_data_in_migration function."""

    @pytest.fixture()
    def migration_apps(self):
        """
        Fixture for a mocked django Apps instance.
        Migrations have a similar registry with the state of the apps
        defined up to that migration.
        """
        apps = mock.MagicMock()

        def _get_model_mocked(model_name):
            return {
                'datahub.core.test.support.book': Book,
                'datahub.core.test.support.person': Person,
            }[model_name]
        apps.get_model.side_effect = _get_model_mocked

        yield apps

    def test_loading(self, migration_apps):
        """
        Test that loading a yaml file updates the existing data.
        """
        yaml_content = """
# person with pk=1, last_name should change
- model: datahub.core.test.support.person
  pk: 1
  fields:
    first_name: Existing
    last_name: Person with changed surname

# person with pk=3, first_name should change, last_name shouldn't change
- model: datahub.core.test.support.person
  pk: 3
  fields:
    first_name: Another existing

# person with pk=10, a new record should be created
- model: datahub.core.test.support.person
  pk: 10
  fields:
    first_name: New
    last_name: Person

# book with pk=1, fk to person (proofreader) should change
- model: datahub.core.test.support.book
  pk: 1
  fields:
    name: Book name
    proofreader: 3
    published_on: '2010-01-01'
"""
        mocked_read = mock.mock_open(read_data=yaml_content)

        people = PersonFactory.create_batch(
            3,
            pk=factory.Iterator([1, 2, 3]),
            first_name='Existing',
            last_name='Person',
        )
        BookFactory(
            pk=1,
            name='Previous book name',
            proofreader=people[0],
            published_on=datetime.date(2010, 1, 1),
            authors=[],
        )

        with mock.patch('datahub.core.migration_utils.open', mocked_read, create=True):
            load_yaml_data_in_migration(migration_apps, 'path-to-file.yaml')

        qs = Person.objects.order_by('id').values('id', 'first_name', 'last_name')
        assert list(qs) == [
            {'id': 1, 'first_name': 'Existing', 'last_name': 'Person with changed surname'},
            {'id': 2, 'first_name': 'Existing', 'last_name': 'Person'},
            {'id': 3, 'first_name': 'Another existing', 'last_name': 'Person'},
            {'id': 10, 'first_name': 'New', 'last_name': 'Person'},
        ]

        qs = Book.objects.order_by('id').values('id', 'name', 'proofreader', 'published_on')
        assert list(qs) == [
            {
                'id': 1,
                'name': 'Book name',
                'proofreader': 3,
                'published_on': datetime.date(2010, 1, 1),
            },
        ]

    def test_pk_required(self, migration_apps):
        """
        Test that if an item in the yaml does not include the pk field,
        the function raises AssertionError.
        """
        yaml_content = """
- model: datahub.core.test.support.person
  fields:
    first_name: Existing
"""
        mocked_read = mock.mock_open(read_data=yaml_content)

        with pytest.raises(AssertionError) as excinfo:
            with mock.patch('datahub.core.migration_utils.open', mocked_read, create=True):
                load_yaml_data_in_migration(migration_apps, 'path-to-file.yaml')
        assert str(excinfo.value) == 'pk field required'

    def test_many_to_many_fields_not_supported(self, migration_apps):
        """
        Test that if an item in the yaml includes a many-to-many field,
        the function raises NotImplementedError as this is not supported yet.
        """
        yaml_content = """
- model: datahub.core.test.support.book
  pk: 1
  fields:
    name: name
    authors:
        - 1
        - 2
    published_on: '2010-01-01'
"""
        mocked_read = mock.mock_open(read_data=yaml_content)

        PersonFactory.create_batch(2, pk=factory.Iterator([1, 2]))

        with pytest.raises(NotImplementedError) as excinfo:
            with mock.patch('datahub.core.migration_utils.open', mocked_read, create=True):
                load_yaml_data_in_migration(migration_apps, 'path-to-file.yaml')
        assert str(excinfo.value) == 'Many-to-many fields not supported'

    def test_one_to_many_fields_not_supported(self, migration_apps):
        """
        Test that if an item in the yaml includes a one-to-many field,
        the function raises NotImplementedError as this is not supported.
        """
        yaml_content = """
- model: datahub.core.test.support.book
  pk: 1
  fields:
    name: name
    published_on: '2010-01-01'

- model: datahub.core.test.support.person
  pk: 1
  fields:
    first_name: A
    last_name: Person
    proofread_books:
        - 1
"""
        mocked_read = mock.mock_open(read_data=yaml_content)

        with pytest.raises(NotImplementedError) as excinfo:
            with mock.patch('datahub.core.migration_utils.open', mocked_read, create=True):
                load_yaml_data_in_migration(migration_apps, 'path-to-file.yaml')
        assert str(excinfo.value) == 'One-to-many fields not supported'

    def test_invalid_file_raises_exception(self, migration_apps):
        """
        Test that if an invalid filename is passed in, the function raises
        FileNotFoundError.
        """
        with pytest.raises(FileNotFoundError):
            load_yaml_data_in_migration(migration_apps, 'invalid-path-to-file.yaml')

    def test_exception_rollsback_changes(self, migration_apps):
        """
        Test that if an exception happens when processing the file, the changes
        are rolled back.
        """
        yaml_content = """
- model: datahub.core.test.support.person
  pk: 1
  fields:
    first_name: Person
    last_name: 1

- model: datahub.core.test.support.person
  pk: 3
  fields:
    invalid_field: error

- model: datahub.core.test.support.person
  pk: 3
  fields:
    first_name: Person
    last_name: 3
"""
        mocked_read = mock.mock_open(read_data=yaml_content)

        assert not Person.objects.count()

        with pytest.raises(FieldDoesNotExist):
            with mock.patch('datahub.core.migration_utils.open', mocked_read, create=True):
                load_yaml_data_in_migration(migration_apps, 'path-to-file.yaml')

        assert not Person.objects.count()

    def test_invalid_fk_raises_exception(self, migration_apps):
        """
        Test that if there's a problem with deserialising the fk field,
        the function raises DeserializationError.
        """
        yaml_content = """
- model: datahub.core.test.support.book
  pk: 1
  fields:
    name: Book name
    proofreader: 'invalid'
    published_on: '2010-01-01'
"""
        mocked_read = mock.mock_open(read_data=yaml_content)

        with pytest.raises(base.DeserializationError) as excinfo:
            with mock.patch('datahub.core.migration_utils.open', mocked_read, create=True):
                load_yaml_data_in_migration(migration_apps, 'path-to-file.yaml')
        assert str(excinfo.value) == (
            "[\"'invalid' value must be an integer.\"]: (book:pk=1) field_value was 'invalid'"
        )

    def test_invalid_field_raises_exception(self, migration_apps):
        """
        Test that if there's a problem with deserialising a field,
        the function raises DeserializationError.
        """
        yaml_content = """
- model: datahub.core.test.support.book
  pk: 1
  fields:
    name: Book name
    published_on: 'invalid'
"""
        mocked_read = mock.mock_open(read_data=yaml_content)

        with pytest.raises(base.DeserializationError) as excinfo:
            with mock.patch('datahub.core.migration_utils.open', mocked_read, create=True):
                load_yaml_data_in_migration(migration_apps, 'path-to-file.yaml')
        assert str(excinfo.value) == (
            "[\"'invalid' value has an invalid date format. It must be in YYYY-MM-DD format.\"]: "
            "(book:pk=1) field_value was 'invalid'"
        )


def test_delete_permissions_contenttypes():
    """
    Tests if the delete_permission_contenttypes function deleted the right
    permissions and contenttypes.
    """
    permissions = Permission.objects.filter(
        content_type__app_label='support',
        content_type__model='permissionmodel',
    )

    contents = ContentType.objects.filter(
        app_label='support',
        model='permissionmodel',
    )

    assert permissions.count() > 0
    assert contents.count() > 0

    DeleteModelWithMetadata.delete_metadata(
        apps,
        'support',
        'permissionmodel',
    )

    assert permissions.count() == 0
    assert contents.count() == 0
