from django.conf import settings
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField, NestedRelatedField
from datahub.investment.project.models import InvestmentProject
from datahub.task.models import InvestmentProjectTask, Task

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class TaskSerializer(serializers.ModelSerializer):
    """Task serilizer"""

    modified_by = NestedAdviserField(read_only=True)
    archived_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    advisers = NestedAdviserField(
        many=True,
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


class InvestmentProjectTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializer()
    modified_by = NestedAdviserField(read_only=True)
    archived_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    investment_project = NestedRelatedField(InvestmentProject)

    class Meta:
        model = InvestmentProjectTask
        fields = (
            'id',
            'investment_project',
            'task',
            'archived_by',
            'created_by',
            'modified_by',
            'created_on',
            'modified_on',
        )
