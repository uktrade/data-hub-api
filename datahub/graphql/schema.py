import graphene

from datahub.company.models import Company, Contact
from .types import CompanyGraphQLType, ContactGraphQLType


def query_all_companies(include_archived=True):
    return Company.objects.all() if include_archived else Company.objects.filter(archived=False)


class Query(graphene.ObjectType):
    all_companies = graphene.List(CompanyGraphQLType)
    company = graphene.Field(CompanyGraphQLType, company_id=graphene.ID())
    all_contacts = graphene.List(ContactGraphQLType)
    company_contacts = graphene.List(ContactGraphQLType, company_id=graphene.ID())
    select_companies = graphene.List(CompanyGraphQLType, page_size=graphene.Int(),
                                     page_offset=graphene.Int(),
                                     include_archived=graphene.Boolean())

    def resolve_all_companies(self, info):
        return query_all_companies()

    def resolve_all_contacts(self, info):
        return Contact.objects.all()

    def resolve_company_contacts(self, info, company_id):
        return Contact.objects.filter(company=company_id)

    def resolve_company(self, info, company_id):
        return Company.objects.get(id=company_id)

    def resolve_select_companies(self, info, page_size=3, page_offset=0, include_archived=True):
        start = page_size * page_offset
        end = start + page_size
        return query_all_companies(include_archived)[start:end]


schema = graphene.Schema(query=Query)
