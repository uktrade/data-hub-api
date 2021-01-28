from rest_framework.schemas.openapi import AutoSchema


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
        return super().map_field(field)
