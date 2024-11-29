import environ

env = environ.Env()
REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')
BUCKET = f"data-flow-bucket-{env('ENVIRONMENT', default='')}"
PREFIX = 'data-flow/exports/'
GREAT_PREFIX = f'{PREFIX}ExportGreatContactFormData/'
STOVA_EVENT_PREFIX = f'{PREFIX}ExportAventriEvents//'
