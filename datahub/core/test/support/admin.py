from django.contrib import admin

from datahub.core.test.support.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Book admin configuration."""
