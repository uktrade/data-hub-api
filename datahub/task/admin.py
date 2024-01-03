from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin
from datahub.task.models import Task
from datahub.task.validators import validate_single_task_relationship


class TaskAdminForm(forms.ModelForm):
    def clean(self):
        super().clean()

        validate_single_task_relationship(
            self.cleaned_data.get('investment_project'),
            self.cleaned_data.get('company'),
            self.cleaned_data.get('interaction'),
            ValidationError,
        )

    class Meta:
        model = Task
        exclude = []


@admin.register(Task)
class TaskAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin form for tasks"""

    search_fields = (
        'pk',
        'title',
    )
    readonly_fields = (
        'id',
        'created',
    )
    list_display = [
        'title',
        'due_date',
    ]

    form = TaskAdminForm
