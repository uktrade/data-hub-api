from opensearch_dsl import Boolean, Date, Integer, Keyword, Text


from datahub.search import dict_utils, fields
from datahub.search.models import BaseSearchModel


class Task(BaseSearchModel):
    """Task model"""

    id = Keyword()
    created_by = fields.contact_or_adviser_field()
    title = Text()
    description = Text()
    due_date = Date()
    reminder_days = Integer()
    email_reminders_enabled = Boolean()
    advisers = fields.contact_or_adviser_field()
    reminder_date = Date()
    investment_project = fields.investment_project_field()
    company = fields.id_name_field()

    MAPPINGS = {
        'created_by': dict_utils.contact_or_adviser_dict,
        'advisers': dict_utils.contact_or_adviser_list_of_dicts,
    }

    COMPUTED_MAPPINGS = {
        'investment_project': dict_utils.task_investment_project_dict,
        'company': dict_utils.task_company,
    }

    SEARCH_FIELDS = (
        'id',
        'title',
        'due_date',
        'created_by',
        'advisers',
    )
