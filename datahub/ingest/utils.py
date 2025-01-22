import gzip
import json

from datahub.ingest.boto3 import S3ObjectProcessor


def compressed_json_faker(records: list[dict] = None, nest_records: bool = True) -> bytes:
    """Serializes and compresses records into a zipped JSON, encoded with UTF-8.

    The `nest_records` argument indicates wether records should be nested under
    an 'object' key, which is common for those transported by Data Flow pipelines.
    """
    json_lines = [
        json.dumps({'object': record}, default=str) if nest_records
        else json.dumps(record, default=str)
        for record in records
    ]
    compressed_content = gzip.compress('\n'.join(json_lines).encode('utf-8'))
    return compressed_content


def upload_objects_to_s3(
    s3_object_processor: S3ObjectProcessor, object_definitions: list[tuple[str, bytes]],
) -> None:
    """Uploads objects (and their contents) to the specified S3 bucket.

    An object definition takes the form (key, content) and an example is:
    ('object/key.json.gz', compressed_json_faker[{'test': 'content'}])
    """
    for definition in object_definitions:
        key, content = definition
        s3_object_processor.s3_client.put_object(
            Bucket=s3_object_processor.bucket,
            Key=key,
            Body=content,
        )
