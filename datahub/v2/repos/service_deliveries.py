import colander

from datahub.interaction.models import ServiceDelivery
from datahub.v2.exceptions import RepoDataValidation
from datahub.v2.schemas.service_deliveries import ServiceDeliverySchema

from . import utils


class ServiceDeliveryDatabaseRepo:
    """DB repo."""

    def __init__(self, config=None):
        """Initialise the repo using the config."""
        self.model_class = ServiceDelivery
        self.schema_class = ServiceDeliverySchema
        self.config = config
        self.url_builder = config['url_builder']

    def validate(self, data):
        """Validate the data against the schema, raising DRF friendly validation errors."""
        try:
            self.schema_class().deserialize(data)
        except colander.Invalid as e:
            raise RepoDataValidation(
                detail=e.asdict()
            )

    def get(self, object_id):
        """Get and return a single object by its id."""
        entity = self.model_class.objects.get(id=object_id)
        data = utils.model_to_json_api_data(entity, self.schema_class(), url_builder=self.url_builder)
        return utils.build_repo_response(data=data)

    def filter(self, company_id=utils.DEFAULT, contact_id=utils.DEFAULT, offset=0, limit=100):
        """Filter objects."""
        filters = {}
        if company_id != utils.DEFAULT:
            filters['company__pk'] = company_id
        if contact_id != utils.DEFAULT:
            filters['contact__pk'] = contact_id
        start, end = offset, offset + limit
        entities = list(self.model_class.objects.filter(**filters).all()[start:end])
        data = [utils.model_to_json_api_data(entity, self.schema_class(), self.url_builder) for entity in entities]
        return utils.build_repo_response(data=data)

    def upsert(self, data):
        """Insert or update an object."""
        model_id = data.get('id', None)
        if model_id:
            data = utils.merge_db_data_and_request_data(
                model_id,
                data,
                self.model_class,
                self.schema_class,
                url_builder=self.url_builder
            )
        self.validate(data)
        return utils.json_api_to_model(data, self.model_class)
