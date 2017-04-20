import pytest

import itertools

from django.apps import apps
from django.conf import settings

from datahub.korben import utils
from datahub.metadata import models as metadata
from datahub.company import models as company
from datahub.interaction import models as interaction

def test_fkey_deps_raises_without_set():
    'Raise if not passed a set'
    with pytest.raises(Exception) as exc:
        utils.fkey_deps([])
    assert  'Pass a set of models' in str(exc)

def test_fkey_deps_raises_on_incomplete_modelset():
    'Raise if fkey_deps isn’t told everything it needs to know'
    with pytest.raises(Exception) as exc:
        utils.fkey_deps(set([
            metadata.Role, company.Advisor, company.Company, company.Contact
        ]))
    assert "is a dependency of " in str(exc)
    assert "but is not being passed" in str(exc)

def test_fkey_deps_success_advisor():
    'The only dependency of Advisor is Team'
    result = dict(utils.fkey_deps(set([metadata.Team, company.Advisor])))
    assert result == {0: {metadata.Team}, 1: {company.Advisor}}

def test_fkey_deps_snapshot():
    'Throw all local app models at fkey_deps'
    local_apps = ('company', 'interaction', 'metadata')
    models = itertools.chain.from_iterable(
        apps.get_app_config(name).models.values() for name in local_apps
    )
    result = dict(
        utils.fkey_deps(
            set(filter(lambda M: not M._meta.auto_created, models))
        )
    )
    assert result == {
        0: {
            metadata.BusinessType,
            metadata.InteractionType,
            metadata.Sector,
            metadata.EmployeeRange,
            metadata.TurnoverRange,
            metadata.UKRegion,
            metadata.Country,
            metadata.Title,
            metadata.Role,
            metadata.Team,
            metadata.Service,
            metadata.ServiceDeliveryStatus,
            metadata.Event,
            metadata.HeadquarterType,
            metadata.CompanyClassification,
            company.CompaniesHouseCompany,
            company.Contact,
        },
        1: {
            company.Company,
            company.Advisor,
            interaction.ServiceOffer,
        },
        2: {
            interaction.Interaction,
            interaction.ServiceDelivery,
        },
    }
