from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Company, Advisor
from datahub.investment.models import InvestmentProject


def create_model_serializer(model, fields=('id', 'name')):
    meta = type('Meta', (), {'fields': fields, 'model': model})
    cls = type('{}Serializer'.format(model.__name__), (), {'Meta': meta})
    return cls


class InvestmentProjectSerializer(serializers.ModelSerializer):
    investment_type = create_model_serializer(meta_models.InvestmentType)
    phase = create_model_serializer(meta_models.InvestmentProjectPhase)
    investor_company = create_model_serializer(Company)
    intermediate_company = create_model_serializer(Company)
    investment_recipient_company = create_model_serializer(Company)
    client_relationship_manager = create_model_serializer(Advisor, fields=('id', 'first_name',
                                                                           'last_name'))
    referral_source_advisor = create_model_serializer(Advisor, fields=('id', 'first_name',
                                                                       'last_name'))
    referral_source_activity = create_model_serializer(meta_models.ReferralSourceActivity)

    class Meta:
        model = InvestmentProject
        fields = ('id', 'name', 'project_code', 'description', 'document_link', 'nda_signed',
                  'estimated_land_date', 'project_shareable', 'anonymous_description',
                  'not_shareable_reason')
