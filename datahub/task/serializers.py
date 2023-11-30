from django.conf import settings
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.investment.project.serializers import (
    NestedInvestmentProjectInvestorCompanyField,
)
from datahub.task.models import Task

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
    )

    def validate(self, data):
        """
        Check that start is before finish.
        """
        print('*****validate', data)
        # if data['start'] > data['finish']:
        #     raise serializers.ValidationError("finish must occur after start")
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
        )
