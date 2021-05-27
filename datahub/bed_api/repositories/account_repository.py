from datahub.bed_api.repositories.base_repository import ReadWriteRepository


class AccountRepository(ReadWriteRepository):
    """
    Account Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Account data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Account/FieldsAndRelationships/view
    """

    entity_name = 'Account'
