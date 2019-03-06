from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.investment.evidence.models import EvidenceDocument, EvidenceTag
from datahub.investment.serializers import NestedInvestmentProjectField, NestedRelatedField


class EvidenceDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Investment Project Evidence Documents."""

    tags = NestedRelatedField(EvidenceTag, many=True, allow_empty=False)
    av_clean = serializers.BooleanField(source='document.av_clean', read_only=True)
    created_by = NestedAdviserField(read_only=True)
    status = serializers.CharField(source='document.status', read_only=True)
    uploaded_on = serializers.DateTimeField(source='document.uploaded_on', read_only=True)
    modified_by = NestedAdviserField(read_only=True)
    investment_project = NestedInvestmentProjectField(read_only=True)

    class Meta:
        model = EvidenceDocument
        fields = (
            'id',
            'tags',
            'comment',
            'av_clean',
            'created_by',
            'created_on',
            'modified_by',
            'modified_on',
            'uploaded_on',
            'investment_project',
            'original_filename',
            'url',
            'status',
        )
        read_only_fields = (
            'url', 'created_on',
        )
        extra_kwargs = {
            'comment': {'default': ''},
        }

    def create(self, validated_data):
        """Create evidence document."""
        evidence_document = EvidenceDocument.objects.create(
            investment_project_id=self.context['request'].parser_context['kwargs']['project_pk'],
            original_filename=validated_data['original_filename'],
            comment=validated_data.get('comment', ''),
            created_by=self.context['request'].user,
        )
        evidence_document.tags.set(validated_data['tags'])
        return evidence_document
