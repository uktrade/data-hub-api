from importlib import import_module

from django.apps import apps
from django.db import connection

from datahub.core.constants import (
    InvestmentType,
)
from datahub.core.test_utils import APITestMixin
from datahub.investment.project.models import GVAMultiplier
from datahub.investment.project.test.factories import (
    GVAMultiplierFactory,
    InvestmentProjectFactory,
)
from datahub.metadata.test.factories import SectorFactory


CAPITAL = GVAMultiplier.SectorClassificationChoices.CAPITAL


class TestGVAMigrations(APITestMixin):
    """Tests migrations added for refactor of GVA calculation process."""

    def test_unlink_gva_multiplier_from_investment_projects(self):
        module = import_module(
            'datahub.investment.project.migrations.0015_remove_existing_gva_multipliers',
        )
        sector = SectorFactory()
        GVAMultiplierFactory(
            multiplier=0.5,
            sector_id=sector.id,
            sector_classification_gva_multiplier=CAPITAL,
        )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=1000,
            investment_type_id=InvestmentType.fdi.value.id,
            sector_id=sector.id,
        )
        assert project.gva_multiplier is not None
        assert project.gross_value_added is not None

        module.unlink_gva_multiplier_from_investment_projects(
            apps,
            connection.schema_editor(),
        )
        project.refresh_from_db()
        assert project.gva_multiplier is None
        assert project.gross_value_added is None

        module.clear_gva_multiplier_data(
            apps,
            connection.schema_editor(),
        )
        assert GVAMultiplier.objects.count() == 0

    def test_add_2022_gva_multipliers(self):
        module = import_module(
            'datahub.investment.project.migrations.0017_add_2022_gva_multipliers_and_relink',
        )
        GVAMultiplier.objects.all().delete()
        assert GVAMultiplier.objects.count() == 0
        module.add_2022_gva_multipliers(
            apps,
            connection.schema_editor(),
        )
        assert GVAMultiplier.objects.count() != 0
        module.reverse_add_2022_gva_multipliers(
            apps,
            connection.schema_editor(),
        )
        assert GVAMultiplier.objects.count() == 0
