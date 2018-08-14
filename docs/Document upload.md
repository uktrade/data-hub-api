# Document Upload

The `document` application provides developer with generic components suitable to use when building document upload functionality into their app.

## Overview

Current implementation lets user to upload documents to S3 buckets. 
Documents are scanned for viruses.

Reference implementation using generic components can be found in `datahub/documents/test/my_entity_document`.

Document upload process is following:
1. Client sends POST request to `/test-my-entity-document` endpoint that creates `MyEntityDocument` with given `original_filename` and corresponding `Document`.
That endpoint returns `id`, `signed_upload_url` and other details.
2. Client performs file upload to the URL from `signed_upload_url` using PUT request and file in the request body.
3. Once upload has been completed, client must call `/test-my-entity-document/<id>/upload-callback` using POST request with empty body. This request will start virus scanning that is performed asynchronously. Endpoint will return `status` with `virus_scanning_scheduled`. Subsequent calls to this endpoint should return the current status of the document.
4. Uploaded document should soon be available to download from `/test-my-entity-document/<id>/download`. This endpoint should return `download_url` with signed URL to the file. Client should redirect user to that URL. If the file is infected, this endpoint will return forbidden HTTP status instead.

In case of multiple file upload, client has to perform above steps for each file individually.

To get:
 - __details__ of the document, client can perform GET request to `/test-my-entity-document/<id>`.
 - __list__ of documents, client can perform GET request to `/test-my-entity-document`.

To __delete__ a document, client should send empty `DELETE` request to `/test-my-entity-document/<id>`.

The URLs can be customised in the `urls.py` file.

## Models

### `Document`

This model only stores information needed to access the document and the outcome of the virus scanning - whether it is safe to access to document.

### `AbstractEntityDocumentModel`

Model that inherits it will contain mandatory details of the document - `id` and `original_filename` and optional custom information (that could be document type, description and so on).
This model also contains one to one link to the `Document` and fields inherited from `BaseModel`.

## ViewSet

The `document` app provides generic view set for the document upload. It provides endpoints for operations listed in the `Overview` section.
Your application's view set should inherit `BaseEntityDocumentModelViewSet` and provide appropriate model, serializer and permissions.

## Bucket configuration

Each application should have its own bucket to store documents.

Configuration is being specified in the `/config/settings/common.py`.

```
DOCUMENT_BUCKETS = {
    ...
    'your_app_bucket_id': {
        'bucket': env('YOUR_APP_BUCKET', default=''),
        'aws_access_key_id': env('YOUR_APP_AWS_ACCESS_KEY_ID', default=''),
        'aws_secret_access_key': env('YOUR_APP_AWS_SECRET_ACCESS_KEY', default=''),
        'aws_region': env('YOUR_APP_AWS_REGION', default=''),
    },
    ...
}
```

Once that is done, a model that inherits `AbstractEntityDocumentModel` needs `BUCKET` property with the app's bucket id.

```
class MyEntityDocument(AbstractEntityDocumentModel):
    """Simple entity document model."""
    
    BUCKET = 'your_app_bucket_id'
    ...
```

Otherwise the entity document will use `default` bucket.
