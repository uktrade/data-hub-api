import uuid

from django.conf import settings
from django.db import models


class CustomerSatisfactionToolFeedback(models.Model):
    """An anonymous feedback submission."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_on = models.DateTimeField(auto_now=True)

    url = models.URLField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        help_text='The URL of the page from which the feedback originates.',
    )

    was_useful = models.BooleanField(help_text='Is this page useful?')

    # detailed feedback fields, iff was_useful=false
    did_not_find_what_i_wanted = models.BooleanField(
        null=True,
        blank=True,
        help_text='I did not find what I was looking for.',
    )
    difficult_navigation = models.BooleanField(
        null=True,
        blank=True,
        help_text='I found it difficult to navigate the page.',
    )
    lacks_feature = models.BooleanField(
        null=True,
        blank=True,
        help_text='The page lacks a feature I need.',
    )
    unable_to_load = models.BooleanField(
        null=True,
        blank=True,
        help_text='I was unable to load/refresh/enter the page.',
    )
    inaccurate_information = models.BooleanField(
        null=True,
        blank=True,
        help_text='I did not find the information accurate.',
    )
    other_issues = models.BooleanField(
        null=True,
        blank=True,
        help_text='Something else went wrong.',
    )
    other_issues_detail = models.TextField(
        null='',
        blank=True,
        help_text='Something else went wrong and this is the detail.',
    )
    improvement_suggestion = models.TextField(
        null='',
        blank=True,
        help_text='Feedback on how to improve the service provided on the page.',
    )

    class Meta:
        verbose_name = 'H-CSAT Result'
        verbose_name_plural = 'H-CSAT Results'
        ordering = ('-created_on',)

    def __str__(self):
        return f'{"Useful" if self.was_useful else "Not useful"} feedback for {self.url} at {self.created_on:%Y-%m-%d %H:%M:%S}'
