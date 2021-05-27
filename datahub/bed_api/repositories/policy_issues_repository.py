from datahub.bed_api.repositories.base_repository import ReadWriteRepository


class PolicyIssuesRepository(ReadWriteRepository):
    """
    Policy Issues Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Policy Issues data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I580000011RrH/FieldsAndRelationships/view
    """

    entity_name = 'Policy_Issues__c'
