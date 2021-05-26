from datahub.bed_api.queries import PolicyIssuesQuery
from datahub.bed_api.repositories.base_repository import BaseRepository


class PolicyIssuesRepository(BaseRepository):
    """
    Policy Issues Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Policy Issues data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I580000011RrH/FieldsAndRelationships/view
    """

    entity_name = 'Policy_Issues__c'
    entity_query = PolicyIssuesQuery
