import environ


env = environ.Env()


AWS_REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')
PREFIX = 'data-flow/exports/'
POSTCODE_DATA_PREFIX = f'{PREFIX}ExportPostcodeDirectory/'
