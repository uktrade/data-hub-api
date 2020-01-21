from django.db import models


class PropositionStatus(models.TextChoices):
    """Proposition statuses."""

    ONGOING = ('ongoing', 'Ongoing')
    ABANDONED = ('abandoned', 'Abandoned')
    COMPLETED = ('completed', 'Completed')
