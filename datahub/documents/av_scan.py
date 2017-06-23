import requests
from django.conf import settings
from django.utils.timezone import now
from rest_framework import status
from requests_toolbelt.multipart.encoder import MultipartEncoder

from datahub.documents.models import Document


class S3StreamingBodyWrapper:
    """S3 Object wrapper that plays nice with streamed multipart/form-data."""

    def __init__(self, s3_obj):
        """Init wrapper, and grab interesting bits from s3 object."""
        self._obj = s3_obj
        self._body = s3_obj['Body']
        self._remaining_bytes = s3_obj['ContentLength']

    def read(self, amt=-1):
        """Read given amount of bytes, and decrease remaining len."""
        content = self._body.read(amt)
        self._remaining_bytes -= len(content)

        return content

    def __len__(self):
        """Return remaining bytes, that have not been read yet."""
        return self._remaining_bytes


def init_document_av_scan(doc_pk: str):
    """Stream file to the AV service."""
    doc = Document.objects.get(pk=doc_pk)
    doc.scan_initiated_on = now()
    doc.save()

    s3_obj = doc.get_s3_object()
    encoder = MultipartEncoder(
        fields={
            'file': (
                doc.filename,
                S3StreamingBodyWrapper(s3_obj),
                s3_obj['ContentType'],
            )
        }
    )

    try:
        response = requests.post(
            # Assumes HTTP Basic auth in URL
            # see: https://github.com/uktrade/dit-clamav-rest
            settings.AV_SERVICE_URL,
            data=encoder,
            headers={'Content-Type': encoder.content_type},
        )
    finally:
        s3_obj['Body'].close()

    if response.status_code == status.HTTP_200_OK:
        doc.scanned_on = now()
        doc.av_clean = response.content == "OK"
        doc.save()

    return response
