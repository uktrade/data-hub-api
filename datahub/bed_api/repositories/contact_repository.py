from datahub.bed_api.repositories.base_repository import BaseRepository


class ContactRepository(BaseRepository):
    """
    Contact Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Contacts data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Contact/FieldsAndRelationships/view
    """

    entity_name = 'Contact'
