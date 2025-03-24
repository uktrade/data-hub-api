import pytest

from datahub.company.merge_company import (
    ALLOWED_RELATIONS_FOR_MERGING,
)
from datahub.company.models import Company
from datahub.core.model_helpers import get_related_fields, get_self_referential_relations


@pytest.mark.django_db
class TestDuplicateCompanyMerger:
    """Tests DuplicateCompanyMerger."""

    def test_company_fields_are_setup_for_merging(self):
        """Test all the models related to a company are accounted for when merging
        companies. This is used by support to merge duplicate companies and
        breaks when relations are not accounted for.

        If your test fails here, you may have related something to a company and this relation
        needs to be accounted for.

        If this relations is to be merged, add it to both:
        ```
            ALLOWED_RELATIONS_FOR_MERGING
            MERGE_CONFIGURATION
        ```

        If the relation is NOT to be merged, it can ignored by adding it ONLY to:
        ```
            ALLOWED_RELATIONS_FOR_MERGING
        ```

        You will also need to add your relation to the `base_expected_result` inside
        `TestDuplicateCompanyMerger` and then add any of your own tests.

        Models for company merge also require the reversion decorator to undo the changes
        if the merge fails:
        ```
            from datahub.core import reversion

            @reversion.register_base_model()
            class ModelRelatedToACompany(models.Model):
        ```
        """
        relations = get_related_fields(Company)

        # All fields in the `Company` model which are related to another `Company`.
        self_related_field_names = [
            field.name for field in get_self_referential_relations(Company)
        ]

        for relation in relations:
            # Ignore fields related to the Company itself, the merge tool blocks these.
            if relation.field.name in self_related_field_names:
                continue

            assert relation.remote_field in ALLOWED_RELATIONS_FOR_MERGING, [(
                'Required relationship missing from company merge. \n'
                f'Field: {relation.field.name} \n'
                f'Model: {relation.model} \n'
                f'Related Name: {relation.related_name} \n'
                f'Related Model: {relation.related_model} \n'
            )]
