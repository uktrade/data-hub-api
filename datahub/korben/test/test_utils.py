import pytest

import itertools

from django.apps import apps
from django.conf import settings

from datahub.korben import utils
from datahub.korben import spec
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
    'Throw all mapped models at fkey_deps'
    result = utils.fkey_deps(set(mapping.ToModel for mapping in spec.mappings))
    assert dict(result) == {
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
        },
        1: {
            company.Company,
            company.Advisor,
            interaction.ServiceOffer,
        },
        2: {
            company.Contact,
        },
        3: {
            interaction.Interaction,
            interaction.ServiceDelivery,
        },
    }
