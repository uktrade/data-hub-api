import boto3
import environ

env = environ.Env()
REGION = env('AWS_DEFAULT_REGION')
BUCKET = 'data-flow-bucket' + env('environment', default='')


class GreatIngestionTask:
    def __init__(self):
        self.s3_client = boto3.client('s3', REGION)

    def ingest(self, file):
        pass
