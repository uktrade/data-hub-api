from datahub.investment.project.evidence.models import EvidenceDocument
from datahub.investment.project.evidence.test.factories import EvidenceTagFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory


def create_evidence_document(user=None, associated=False, investment_project=None):
    """Creates evidence document."""
    evidence_tags = EvidenceTagFactory.create_batch(2)
    if not investment_project:
        investment_project = InvestmentProjectFactory(
            **{'created_by': user} if associated else {},
        )
    entity_document = EvidenceDocument.objects.create(
        investment_project_id=investment_project.pk,
        original_filename='test.txt',
        created_by=user,
    )
    entity_document.tags.set(evidence_tags)
    return entity_document
