from django.urls import reverse
from django.utils.timezone import now

from company.test.factories import CompanyFactory, ContactFactory, InteractionFactory
from core.test_utils import LeelooTestCase, get_test_user


class DashboardTestCase(LeelooTestCase):

    def test_intelligent_homepage(self):

        user = get_test_user()
        company = CompanyFactory(advisor=user.advisor, created_on=now())
        contact = ContactFactory(company=company)
        interaction = InteractionFactory(dit_advisor=user.advisor)

        url = reverse('dashboard:intelligent-homepage')
        response = self.api_client.get(url)
