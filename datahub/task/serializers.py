from functools import partial

from django.conf import settings
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField, NestedRelatedField
from datahub.investment.project.serializers import (
    NestedInvestmentProjectInvestorCompanyField,
)
from datahub.task.models import InvestmentProjectTask, Task

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


NestedInvestmentProjectTaskField = partial(
    NestedRelatedField,
    model=InvestmentProjectTask,
    extra_fields=(
        (
            'investment_project',
            NestedInvestmentProjectInvestorCompanyField(),
        ),
    ),
)


class BasicTaskSerializer(serializers.ModelSerializer):
    """Basic task serilizer that contains the fields shared among all other task serializers"""

    modified_by = NestedAdviserField(read_only=True)
    archived_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    advisers = NestedAdviserField(
        many=True,
        allow_empty=False,
    )
    archived = serializers.BooleanField(read_only=True)

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
        )


class TaskSerializer(BasicTaskSerializer):
    """Task serializer"""

    investment_project_task = NestedInvestmentProjectTaskField(
        read_only=True,
        source='task_investmentprojecttask',
    )

    class Meta:
        model = BasicTaskSerializer.Meta.model
        fields = BasicTaskSerializer.Meta.fields + ('investment_project_task',)


class InvestmentProjectTaskSerializer(serializers.ModelSerializer):
    task = BasicTaskSerializer()
    modified_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    investment_project = NestedInvestmentProjectInvestorCompanyField()

    class Meta:
        model = InvestmentProjectTask
        fields = (
            'id',
            'investment_project',
            'task',
            'created_by',
            'modified_by',
            'created_on',
            'modified_on',
        )


class InvestmentProjectTaskQueryParamSerializer(serializers.Serializer):
    investment_project = serializers.UUIDField(required=False)
