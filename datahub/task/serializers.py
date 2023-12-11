from django.conf import settings
from rest_framework import serializers

from datahub.company.models.company import Company

from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.investment.project.serializers import (
    NestedInvestmentProjectInvestorCompanyField,
)
from datahub.task.models import Task
from datahub.task.validators import validate_single_task_relationship

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class TaskSerializer(serializers.ModelSerializer):
    """Basic task serilizer that contains the fields shared among all other task serializers"""

    modified_by = NestedAdviserField(read_only=True)
    archived_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    advisers = NestedAdviserField(
        many=True,
        allow_empty=False,
    )
    archived = serializers.BooleanField(read_only=True)
    investment_project = NestedInvestmentProjectInvestorCompanyField(
        required=False,
        allow_null=True,
    )
    company = NestedRelatedField(
        Company,
        required=False,
        allow_null=True,
    )

    def to_representation(self, instance):
        company = instance.get_company()
        ret = super().to_representation(instance)
        if company:
            ret['company'] = {'id': company.id, 'name': company.name}
        return ret

    def validate(self, data):
        validate_single_task_relationship(
            data.get('investment_project', None),
            data.get('company', None),
            serializers.ValidationError,
        )
        return data

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'due_date',
            'reminder_days',
            'email_reminders_enabled',
            'advisers',
            'archived',
            'archived_reason',
            'archived_by',
            'created_by',
            'modified_by',
            'created_on',
            'modified_on',
            'investment_project',
            'company',
        )
