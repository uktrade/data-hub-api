from unittest.mock import Mock

import pytest
import reversion
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.core.management.base import CommandError
from reversion.models import Revision, Version

from datahub.cleanup.management.commands import delete_orphaned_versions
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyExportCountryFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionExportCountryFactory,
)
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory
from datahub.investment.project.test.factories import (
    InvestmentActivityFactory, InvestmentProjectFactory, InvestmentProjectTeamMemberFactory,
)
from datahub.metadata.test.factories import SectorFactory
from datahub.omis.order.test.factories import OrderFactory


MAPPINGS = {
    'company.Advisor': AdviserFactory,
    'company.Company': CompanyFactory,
    'company.CompanyExportCountry': CompanyExportCountryFactory,
    'company.Contact': ContactFactory,
    'event.Event': EventFactory,
    'interaction.Interaction': CompanyInteractionFactory,
    'interaction.InteractionExportCountry': InteractionExportCountryFactory,
    'investment.InvestmentProject': InvestmentProjectFactory,
    'investment.InvestmentProjectTeamMember': InvestmentProjectTeamMemberFactory,
    'investment.InvestmentActivity': InvestmentActivityFactory,
    'investor_profile.LargeCapitalInvestorProfile': LargeCapitalInvestorProfileFactory,
    'metadata.Sector': SectorFactory,
    'order.Order': OrderFactory,
}


def test_mappings():
    """
    Test that `MAPPINGS` includes all the data necessary for covering all the cases.
    This is to avoid missing tests when new fields and models are added or changed.
    """
    assert set(delete_orphaned_versions._get_all_model_labels()) == set(MAPPINGS)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'model_label,model_factory',
    MAPPINGS.items(),
)
def test_with_one_model(model_label, model_factory):
    """
    Test that --model_label can be used to specify which model we want the versions deleted.
    """
    model = apps.get_model(model_label)

    with reversion.create_revision():
        objs = model_factory.create_batch(2)

    # check created versions/revisions
    assert Version.objects.get_for_model(model).count() == 2
    assert Revision.objects.count() == 1

    objs[0].delete()  # delete just one

    # check that versions/revisions haven't changed
    assert Version.objects.get_for_model(model).count() == 2
    assert Revision.objects.count() == 1

    management.call_command(delete_orphaned_versions.Command(), model_label=[model_label])

    # the revision wasn't deleted because it's still referenced by other objects
    assert Version.objects.get_for_model(model).count() == 1
    assert Revision.objects.count() == 1


@pytest.mark.django_db
def test_with_all_models(caplog):
    """
    Test that if --model_label is not specified, the command cleans up the versions
    for all registered models.
    """
    caplog.set_level('INFO')

    objs = []
    for model_factory in MAPPINGS.values():
        with reversion.create_revision():
            obj, _ = model_factory.create_batch(2)  # keep only one
            objs.append(obj)

    total_versions = Version.objects.count()

    for obj in objs:
        obj.delete()

    assert Version.objects.count() == total_versions

    management.call_command(delete_orphaned_versions.Command())

    assert Version.objects.count() == total_versions - len(MAPPINGS)
    assert Revision.objects.count() == len(MAPPINGS)

    assert f'{len(MAPPINGS)} records deleted' in caplog.text
    assert f'reversion.Version: {len(MAPPINGS)}' in caplog.text


@pytest.mark.django_db
def test_delete_revisions_without_versions(caplog):
    """
    Test that a revision gets deleted as well if there aren't any more versions referencing it.
    """
    caplog.set_level('INFO')

    model_label, model_factory = next(iter(MAPPINGS.items()))
    model = apps.get_model(model_label)

    with reversion.create_revision():
        obj = model_factory()

    # delete all versions indirectly created
    Version.objects.exclude(
        content_type=ContentType.objects.get_for_model(model),
        object_id=obj.pk,
    ).delete()

    # check that only 1 version and revision exist
    assert Version.objects.count() == 1
    assert Revision.objects.count() == 1

    obj.delete()

    # check that versions/revisions haven't changed
    assert Version.objects.count() == 1
    assert Revision.objects.count() == 1

    management.call_command(delete_orphaned_versions.Command(), model_label=[model_label])

    # the revision is deleted as well because there aren't any more versions
    assert Version.objects.count() == 0
    assert Revision.objects.count() == 0

    assert 'reversion.Version: 1' in caplog.text
    assert 'reversion.Revision: 1' in caplog.text


@pytest.mark.django_db
def test_rollback_in_case_or_error(monkeypatch):
    """Test that if there's an exception in the logic, all the changes are rolled back."""
    objs = []
    for model_factory in MAPPINGS.values():
        with reversion.create_revision():
            objs.append(model_factory())

    total_versions = Version.objects.count()

    for obj in objs:
        obj.delete()

    monkeypatch.setattr(Revision.objects, 'filter', Mock(side_effect=Exception))

    with pytest.raises(Exception):
        management.call_command(delete_orphaned_versions.Command())

    assert Version.objects.count() == total_versions


def test_fails_with_invalid_model():
    """Test that if an invalid value for model is passed in, the command errors."""
    with pytest.raises(CommandError):
        management.call_command(delete_orphaned_versions.Command(), 'invalid')
