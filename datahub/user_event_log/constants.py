from model_utils import Choices

USER_EVENT_TYPES = Choices(
    ('search_export', 'Exported search results'),
    ('proposition_document_delete', 'Deleted proposition document'),
    ('evidence_document_delete', 'Deleted evidence document'),
)
