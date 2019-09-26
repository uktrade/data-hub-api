from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test.factories import to_many_field


class ExportingCompanyFactory(CompanyFactory):
    """Company factory adding export countries data."""

    @to_many_field
    def export_to_countries(self):  # noqa: D102
        return [
            constants.Country.canada.value.id,
            constants.Country.france.value.id
        ]
