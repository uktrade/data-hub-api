from django.conf import settings
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.task.models import Task

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class TaskSerializer(serializers.ModelSerializer):
    modified_by = NestedAdviserField(read_only=True)
    archived_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    advisers = NestedAdviserField(
        many=True,
    )

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
        )
