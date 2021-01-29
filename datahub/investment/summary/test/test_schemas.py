from unittest.mock import Mock

from datahub.investment.summary.schemas import IProjectSummarySchema


def test_annual_summaries_schema():
    """
    Annual summaries schema should include financial years and totals.
    """
    schema = IProjectSummarySchema()
    annual_summaries_field = Mock()
    annual_summaries_field.field_name = 'annual_summaries'
    field_schema = schema.map_field(annual_summaries_field)
    expected_schema = {
        'type': 'array',
        'items': {
            'type': 'object',
            'readOnly': True,
            'properties': {
                'financial_year': {
                    'type': 'object',
                    'properties': {
                        'label': {'type': 'string', 'example': '2020-21'},
                        'start': {'type': 'date', 'example': '2020-04-01'},
                        'end': {'type': 'date', 'example': '2021-03-31'},
                    },
                },
                'totals': {
                    'type': 'object',
                    'properties': {
                        'prospect': {'type': 'integer'},
                        'assign_pm': {'type': 'integer'},
                        'active': {'type': 'integer'},
                        'verify_win': {'type': 'integer'},
                        'won': {'type': 'integer'},
                    },
                },
            },
        },
    }
    assert field_schema == expected_schema
