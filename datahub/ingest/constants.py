import environ

env = environ.Env()


AWS_REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')
DATA_FLOW_EXPORTS_PREFIX = 'data-flow/exports/'
S3_BUCKET_NAME = f'data-flow-bucket-{env("ENVIRONMENT", default="")}'

TEST_AWS_REGION = 'eu-west-2'
TEST_PREFIX = 'test/'
TEST_OBJECT_KEY = f'{TEST_PREFIX}object.json.gz'
TEST_S3_BUCKET_NAME = 'test-bucket'
