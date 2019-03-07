from model_utils import Choices


PropositionStatus = Choices(
    ('ongoing', 'Ongoing'),
    ('abandoned', 'Abandoned'),
    ('completed', 'Completed'),
)


FEATURE_FLAG_PROPOSITION_DOCUMENT = 'proposition-documents'
