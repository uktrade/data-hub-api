import graphene

from datahub.company.models import Company, Contact
from .types import CompanyGraphQLType, ContactGraphQLType


class Query(graphene.ObjectType):
    all_companies = graphene.List(CompanyGraphQLType)
    company = graphene.Field(CompanyGraphQLType, company_id=graphene.ID())
    all_contacts = graphene.List(ContactGraphQLType)
    company_contacts = graphene.List(ContactGraphQLType, company_id=graphene.ID())

    def resolve_all_companies(self, info):
        return Company.objects.all()

    def resolve_all_contacts(self, info):
        return Contact.objects.all()

    def resolve_company_contacts(self, info, company_id):
        return Contact.objects.filter(company=company_id)

    def resolve_company(self, info, company_id):
        return Company.objects.get(id=company_id)


schema = graphene.Schema(query=Query)
