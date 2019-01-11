from random import shuffle

from django.urls import reverse

from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.search.sync_object import sync_object
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp


class TestNormalizedField(APITestMixin):
    """Tests the behaviour of NormalizedKeyword."""

    def test_sorting(self, setup_es):
        """Test to demonstrate how NormalizedKeyword sorts."""
        names = [
            'Alice',
            'Barbara',
            'barbara 2',
            'Álice 2',
            'ａlice 3',
        ]
        shuffle(names)

        for name in names:
            obj = SimpleModel(name=name)
            obj.save()
            sync_object(SimpleModelSearchApp, obj.pk)

        setup_es.indices.refresh()

        user = create_test_user(permission_codenames=['view_simplemodel'])
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:simplemodel')

        response = api_client.post(
            url,
            data={
                'sortby': 'name.keyword',
            },
        )
        response_data = response.json()
        results = response_data['results']

        assert [result['name'] for result in results] == [
            'Alice',
            'Álice 2',
            'ａlice 3',
            'Barbara',
            'barbara 2',
        ]
