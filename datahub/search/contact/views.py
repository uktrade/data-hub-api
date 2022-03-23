from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Case, CharField, Max, When
from django.db.models.functions import Cast

from datahub.company import consent
from datahub.company.models import Contact as DBContact
from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_front_end_url_expression,
    get_string_agg_subquery,
    get_top_related_expression_subquery,
)
from datahub.core.utils import slice_iterable_into_chunks
from datahub.interaction.models import Interaction as DBInteraction
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.search.contact import ContactSearchApp
from datahub.search.contact.serializers import SearchContactQuerySerializer
from datahub.search.views import register_v3_view, SearchAPIView, SearchExportAPIView


class SearchContactAPIViewMixin:
    """Defines common settings."""

    search_app = ContactSearchApp
    serializer_class = SearchContactQuerySerializer
    es_sort_by_remappings = {
        'company.name': 'company.name.keyword',
        'last_name': 'last_name.keyword',
    }

    FILTER_FIELDS = (
        'email',
        'name',
        'company',
        'company_name',
        'company_sector',
        'company_sector_descends',
        'company_uk_region',
        'created_by',
        'created_on_exists',
        'address_country',
        'archived',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'company_sector': 'company_sector.id',
        'company_uk_region': 'company_uk_region.id',
        'address_country': 'address_country.id',
        'created_by': 'created_by.id',
    }

    COMPOSITE_FILTERS = {
        'name': [
            'name',
            'name.trigram',
        ],
        'company_name': [
            'company.name',
            'company.name.trigram',
            'company.trading_names',  # to find 2-letter words
            'company.trading_names.trigram',
        ],
        'company_sector_descends': [
            'company_sector.id',
            'company_sector.ancestors.id',
        ],
    }


@register_v3_view()
class SearchContactAPIView(SearchContactAPIViewMixin, SearchAPIView):
    """Filtered contact search view."""


@register_v3_view(sub_path='export')
class SearchContactExportAPIView(SearchContactAPIViewMixin, SearchExportAPIView):
    """Company search export view."""

    def _is_valid_email(self, value):
        """Validate if emails are valid and return a boolean flag."""
        try:
            validate_email(value)
            return True
        except ValidationError:
            return False

    consent_page_size = 100

    db_sort_by_remappings = {
        'address_country.name': 'computed_country_name',
        'address_area.name': 'computed_area_name',
    }
    queryset = DBContact.objects.annotate(
        # name=get_full_name_expression(),
        link=get_front_end_url_expression('contact', 'pk'),
        company_sector_name=get_sector_name_subquery('company__sector'),
        company_link=get_front_end_url_expression('company', 'company__pk'),
        computed_country_name=Case(
            When(address_same_as_company=True, then='company__address_country__name'),
            default='address_country__name',
        ),
        computed_area_name=Case(
            When(address_same_as_company=True, then='company__address_area__name'),
            default='address_area__name',
        ),
        computed_postcode=Case(
            When(address_same_as_company=True, then='company__address_postcode'),
            default='address_postcode',
        ),
        date_of_latest_interaction=get_aggregate_subquery(
            DBContact,
            Max('interactions__date'),
        ),
        teams_of_latest_interaction=get_top_related_expression_subquery(
            DBInteraction.contacts.field,
            get_string_agg_subquery(
                DBInteraction,
                Cast('dit_participants__team__name', CharField()),
                distinct=True,
            ),
            ('-date',),
        ),
    )
    field_titles = {
        'name': 'Name',
        'job_title': 'Job title',
        'created_on': 'Date created',
        'archived': 'Archived',
        'link': 'Link',
        'company__name': 'Company',
        'company_sector_name': 'Company sector',
        'company_link': 'Company link',
        'company__uk_region__name': 'Company UK region',
        'computed_country_name': 'Country',
        'computed_area_name': 'Area',
        'computed_postcode': 'Postcode',
        'full_telephone_number': 'Phone number',
        'email': 'Email address',
        'accepts_dit_email_marketing': 'Accepts DIT email marketing',
        'date_of_latest_interaction': 'Date of latest interaction',
        'teams_of_latest_interaction': 'Teams of latest interaction',
        'created_by__dit_team__name': 'Created by team',
    }

    def _add_consent_response(self, rows):
        """
        Transforms iterable to add user consent from the consent service.

        The consent lookup makes an external API call to return consent.
        For perfromance reasons the consent amount is limited by consent_page_size.
        Due to this limitaion the iterable are sliced into chunks requesting consent for 100 rows
        at a time.
        """
        # Slice iterable into chunks
        row_chunks = slice_iterable_into_chunks(rows, self.consent_page_size)
        for chunk in row_chunks:
            """
            Loop over the chunks and extract the email and item.
            Save the item because the iterator cannot be used twice.
            """
            rows = list(chunk)
            # Peform constent lookup on emails POST request
            consent_lookups = consent.get_many(
                [row['email'] for row in rows if self._is_valid_email(row['email'])],
            )
            for row in rows:
                # Assign contact consent boolean to accepts_dit_email_marketing
                # and yield modified result.
                row['accepts_dit_email_marketing'] = consent_lookups.get(row['email'], False)
                yield row

    def _get_rows(self, ids, search_ordering):
        """
        Get row queryset for constent service.

        This populates accepts_dit_email_marketing field from the consent service and
        removes the accepts_dit_email_marketing from the field query because the field is not in
        the db.
        """
        db_ordering = self._translate_search_ordering_to_django_ordering(search_ordering)
        field_titles = self.field_titles.copy()
        del field_titles['accepts_dit_email_marketing']
        rows = self.queryset.filter(
            pk__in=ids,
        ).order_by(
            *db_ordering,
        ).values(
            *field_titles,
        ).iterator()

        return self._add_consent_response(rows)
