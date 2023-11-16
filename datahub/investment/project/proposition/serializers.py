from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from datahub.company.serializers import NestedAdviserField
from datahub.documents.models import UploadStatus
from datahub.investment.project.proposition.models import Proposition, PropositionDocument
from datahub.investment.project.serializers import NestedInvestmentProjectField


class CreatePropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for create endpoint."""

    class Meta:
        model = Proposition
        fields = (
            'adviser',
            'deadline',
            'name',
            'scope',
        )


class CompletePropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for complete endpoint."""

    class Meta:
        model = Proposition
        fields = (
            'details',
        )
        extra_kwargs = {
            'details': {'default': ''},
        }

    def complete(self):
        """Complete a proposition."""
        self.instance.complete(
            by=self.context['current_user'],
            details=self.validated_data['details'],
        )
        return self.instance

    def validate_doc(self):
        message_document = "A supporting document hasn't yet been uploaded, \
                            please upload one to continue"
        message_scanning = "A supporting document hasn't finished scanning, \
                            please try again in a few moments."
        if self.instance.documents.filter(
                document__status=UploadStatus.VIRUS_SCANNED).count() == 0:
            raise ValidationError({
                'non_field_errors': [message_document],
            })
        if self.instance.documents.filter(
                document__status=UploadStatus.VIRUS_SCANNING_IN_PROGRESS):
            raise ValidationError({
                'non_field_errors': [message_scanning],
            })

    def validate(self, data):
        """
        Validate provided data.

        Checks that the referral has the expected status.
        """
        self.validate_doc()

        return super().validate(data)


class AbandonPropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for abandon endpoint."""

    class Meta:
        model = Proposition
        fields = (
            'details',
        )
        extra_kwargs = {
            'details': {'allow_blank': False},
        }

    def abandon(self):
        """Abandon a proposition."""
        self.instance.abandon(
            by=self.context['current_user'],
            details=self.validated_data['details'],
        )
        return self.instance


class PropositionDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Investment Project Proposition Documents."""

    av_clean = serializers.BooleanField(source='document.av_clean', read_only=True)
    created_by = NestedAdviserField(read_only=True)
    status = serializers.CharField(source='document.status', read_only=True)
    uploaded_on = serializers.DateTimeField(source='document.uploaded_on', read_only=True)

    class Meta:
        model = PropositionDocument
        fields = (
            'id',
            'av_clean',
            'created_by',
            'created_on',
            'uploaded_on',
            'original_filename',
            'url',
            'status',
        )
        read_only_fields = ('url', 'created_on')

    def create(self, validated_data):
        """Create proposition document."""
        return PropositionDocument.objects.create(
            proposition_id=self.context['request'].parser_context['kwargs']['proposition_pk'],
            original_filename=validated_data['original_filename'],
            created_by=self.context['request'].user,
        )


class PropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for view only endpoints."""

    investment_project = NestedInvestmentProjectField()
    adviser = NestedAdviserField()
    created_by = NestedAdviserField()
    modified_by = NestedAdviserField()

    class Meta:
        model = Proposition
        fields = (
            'id',
            'investment_project',
            'adviser',
            'deadline',
            'status',
            'name',
            'scope',
            'details',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
        )
        read_only_fields = fields
