from datahub.bed_api.constants import AccountQuery
from datahub.bed_api.repositories.base_repository import BaseRepository


class AccountRepository(BaseRepository):
    """
    Account Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Account data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Account/FieldsAndRelationships/view
    """

    entity_name = 'Account'
    entity_query = AccountQuery
