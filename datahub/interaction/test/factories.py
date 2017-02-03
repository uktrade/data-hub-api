import factory
from django.utils.timezone import now

from datahub.company.test.factories import CompanyFactory, ContactFactory, AdvisorFactory
from datahub.core import constants


class InteractionFactory(factory.django.DjangoModelFactory):
    """Interaction factory."""

    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = 'foo'
    date = now()
    notes = 'Bar'
    dit_advisor = factory.SubFactory(AdvisorFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team_id = constants.Team.healthcare_uk.value.id
    created_on = now()
    interaction_type_id = constants.InteractionType.face_to_face.value.id

    class Meta:
        model = 'interaction.Interaction'
