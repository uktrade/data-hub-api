from datahub.company_activity.serializers import CompanyActivitySerializer


class TestCompanyAcitivitySerializer:
    """Tests for the Company Activity Serializer"""

    def test_serialization_without_request(self):
        """
        Test Company Activity Serializer when not in the context of a request
        """
        serializer = CompanyActivitySerializer(context={'request': None})
        assert serializer.get_adviser_from_post_data() == []
