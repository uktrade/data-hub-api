from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class DnBMatchingResult(models.Model):
    """
    Model containing support data for resolved D&B matching information.

    The data field can contain information about a positive match
    (e.g. duns_number) or reasons why a match can't be found
    (e.g. invalid business).
    """

    created_on = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=True)
    company = models.OneToOneField('company.Company', on_delete=models.CASCADE)
    data = JSONField(encoder=DjangoJSONEncoder)

    def __str__(self):
        """Human-friendly string representation."""
        return f'{self.company} – {self.data}'


class DnBMatchingCSVRecord(models.Model):
    """
    Model containing the actual matching data provided by D&B.

    As more iterations are planned over a long period of time (weeks),
    each batch is grouped by batch_number.
    """

    created_on = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    company_id = models.UUIDField()
    batch_number = models.PositiveIntegerField()
    data = JSONField(encoder=DjangoJSONEncoder)

    def __str__(self):
        """Human-friendly string representation."""
        return f'{self.company_id} – {self.data}'
