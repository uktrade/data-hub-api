from datahub.core.mixins import ArchivableViewSetMixin
from datahub.core.viewsets import CoreViewSetV3
from datahub.documents import models
from datahub.documents.serializers import DocumentSerializer


class IProjectDocumentViewSet(ArchivableViewSetMixin, CoreViewSetV3):
    serializer_class = DocumentSerializer
    queryset = models.Document.objects.all()
