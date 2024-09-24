import boto3
import environ

env = environ.Env()
REGION = env('AWS_DEFAULT_REGION')
PREFIX = 'data-flow/exports/'
GREAT_PREFIX = PREFIX + 'GreatGovUKFormsPipeline/'


class CompanyActivityIngestionTask:
    def __init__(self):
        self.s3_client = boto3.client("s3", REGION)

    def list_objects(self, bucket_name, prefix):
        """Returns a list all objects with specified prefix."""
        response = self.s3_client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix,
        )
        return [object["Key"] for object in response["Contents"]]

    def ingest_activity_data(self):
        pass


