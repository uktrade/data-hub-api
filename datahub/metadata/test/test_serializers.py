from datahub.metadata.models import CountryState
from datahub.metadata.serializers import CountryStateSerializer


class TestCountryStateSerializer:
    """Serializer tests"""

    def test_state_serializes_correctly(self):
        """Test to ensure the state data serializes correctly"""
        serialized_alabama = {
            'id': '9309365-7aa7-49594-a5e5-7c758ea74235',
            'disabled_on': False,
            'name': 'Alabama',
            'country': None,
            'state_code': 'AL',
        }

        alabama = CountryState(
            pk='9309365-7aa7-49594-a5e5-7c758ea74235',
            disabled_on=False,
            name='Alabama',
            state_code='AL',
        )
        serializer_result = CountryStateSerializer(alabama)

        assert serializer_result.data == serialized_alabama
