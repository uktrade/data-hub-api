import json

from django.contrib import admin
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from datahub.company import tasks
from .models import TaskInfo


@admin.register(TaskInfo)
class TaskInfoAdmin(admin.ModelAdmin):
    """Admin for TaskInfo."""

    readonly_fields = ('changes_prettified', 'status', 'task_id', 'user', 'update')
    exclude = ('changes', 'db_table')
    list_display = ('task_id', 'user', 'type', 'created_on', 'status')
    actions = ['respawn_task']
    list_filter = ['created_on', 'db_table']
    search_fields = ['user', 'task_id']

    def type(self, instance):
        """Human readable save type from db_table."""
        type = instance.db_table.split('_')[0] if '_' in instance.db_table else instance.db_table
        return mark_safe(type)
    type.short_description = 'type'

    def changes_prettified(self, instance):
        """Show JSON changes in a human readable way.

        From https://www.pydanny.com/pretty-formatting-json-django-admin.html
        """
        response = json.dumps(instance.changes, sort_keys=True, indent=2)
        formatter = HtmlFormatter(style='colorful', noclasses=True)
        response = highlight(response, JsonLexer(), formatter)
        style = '<style>' + formatter.get_style_defs() + '</style><br>'
        return mark_safe(style + response)
    changes_prettified.short_description = 'changes prettified'

    def respawn_task(self, request, queryset):
        """Respawn a task getting the information from TaskInfo."""
        for t in queryset:
            tasks.save_to_korben.delay(
                data=t.changes,
                user_id=t.user_id,
                db_table=t.db_table,
                update=t.update
            )
    respawn_task.short_description = 'Re-spawn the task (DANGEROUS!)'
