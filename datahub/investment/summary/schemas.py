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
                        'financial_year': {'type': 'string', 'example': '2020-21'},
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
        else:
            return super().map_field(field)
