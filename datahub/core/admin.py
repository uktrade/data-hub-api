import json
from pygments import highlight

from django.contrib import admin
from django.utils.safestring import mark_safe
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from .models import TaskInfo


@admin.register(TaskInfo)
class TaskInfoAdmin(admin.ModelAdmin):
    """Show JSON changes in a human readable way.

    From https://www.pydanny.com/pretty-formatting-json-django-admin.html
    """
    readonly_fields = ('changes_prettified', 'status')
    exclude = ('changes',)
    list_display = ('name', 'user', 'created_on', 'status')

    def changes_prettified(self, instance):
        """Function to display pretty version of the changes."""
        response = json.dumps(instance.changes, sort_keys=True, indent=2)
        formatter = HtmlFormatter(style='colorful', noclasses=True)
        response = highlight(response, JsonLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style><br>"
        return mark_safe(style + response)

    changes_prettified.short_description = 'changes prettified'

