from logging import getLogger

from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from datahub.investment.project.models import InvestmentProject
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


logger = getLogger(__name__)


class SearchInvestmentProjectQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate investment project search POST bodies."""

    adviser = SingleOrListField(child=StringUUIDField(), required=False)
    client_relationship_manager = SingleOrListField(child=StringUUIDField(), required=False)
    created_on_after = RelaxedDateTimeField(required=False)
    created_on_before = RelaxedDateTimeField(required=False)
    actual_land_date_after = RelaxedDateTimeField(required=False)
    actual_land_date_before = RelaxedDateTimeField(required=False)
    estimated_land_date_after = RelaxedDateTimeField(required=False)
    estimated_land_date_before = RelaxedDateTimeField(required=False)
    investment_type = SingleOrListField(child=StringUUIDField(), required=False)
    investor_company = SingleOrListField(child=StringUUIDField(), required=False)
    investor_company_country = SingleOrListField(child=StringUUIDField(), required=False)
    country_investment_originates_from = SingleOrListField(child=StringUUIDField(), required=False)
    likelihood_to_land = SingleOrListField(child=StringUUIDField(), required=False)
    sector = SingleOrListField(child=StringUUIDField(), required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    stage = SingleOrListField(child=StringUUIDField(), required=False)
    status = SingleOrListField(child=serializers.CharField(), required=False)
    uk_region_location = SingleOrListField(child=StringUUIDField(), required=False)
    level_of_involvement_simplified = SingleOrListField(
        child=serializers.ChoiceField(choices=InvestmentProject.INVOLVEMENT),
        required=False,
    )
    gross_value_added_start = serializers.IntegerField(required=False, min_value=0)
    gross_value_added_end = serializers.IntegerField(required=False, min_value=0)

    SORT_BY_FIELDS = (
        'created_on',
        'estimated_land_date',
        'name',
        'stage.name',
    )
