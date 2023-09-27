from django.conf import settings
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField, NestedRelatedField
from datahub.investment.project.serializers import NestedInvestmentProjectField
from datahub.task.models import InvestmentProjectTask, Task

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


# NestedInvestmentProjectTaskField = partial(
#     NestedRelatedField,
#     InvestmentProject,
#     extra_fields=('investment_project'),
# )
class TaskSerializer(serializers.ModelSerializer):
    """Task serilizer"""

    modified_by = NestedAdviserField(read_only=True)
    archived_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    advisers = NestedAdviserField(
        many=True,
        allow_empty=False,
    )
    archived = serializers.BooleanField(read_only=True)
    investment_project_task = NestedRelatedField(
        model=InvestmentProjectTask,
        source='task_investmentprojecttask',
        extra_fields=(
            (
                'investment_project',
                NestedInvestmentProjectField(
                    extra_fields=(
                        (
                            'investor_company',
                            NestedRelatedField(
                                'company.Company',
                            ),
                        ),
                    ),
                ),
            ),
        ),
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
            'created_on',
            'modified_on',
            'investment_project_task',
        )


class InvestmentProjectTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializer()
    modified_by = NestedAdviserField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    investment_project = NestedInvestmentProjectField(read_only=True)

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
