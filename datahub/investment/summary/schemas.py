from rest_framework.schemas.openapi import AutoSchema


PROJECT_COUNT_SCHEMA = {
    'type': 'object',
    'properties': {
        'label': {'type': 'string'},
        'id': {'type': 'string'},
        'value': {'type': 'integer'},
    },
}


class IProjectSummarySchema(AutoSchema):
    """
    Schema for Investment Project Summaries
    """

    def map_field(self, field):
        """
        Since annual_summaries is a custom field, add its schema manually
        """
        if field.field_name == 'annual_summaries':
            return {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'readOnly': True,
                    'properties': {
                        'financial_year': {
                            'type': 'object',
                            'properties': {
                                'label': {'type': 'string', 'example': '2020-21'},
                                'start': {
                                    'type': 'string',
                                    'format': 'date',
                                    'example': '2020-04-01',
                                },
                                'end': {
                                    'type': 'string',
                                    'format': 'date',
                                    'example': '2021-03-31',
                                },
                            },
                        },
                        'totals': {
                            'type': 'object',
                            'properties': {
                                'prospect': PROJECT_COUNT_SCHEMA,
                                'assign_pm': PROJECT_COUNT_SCHEMA,
                                'active': PROJECT_COUNT_SCHEMA,
                                'verify_win': PROJECT_COUNT_SCHEMA,
                                'won': PROJECT_COUNT_SCHEMA,
                            },
                        },
                    },
                },
            }
        return super().map_field(field)
