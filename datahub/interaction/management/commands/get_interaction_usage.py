from logging import getLogger

from django.core.management.base import BaseCommand
from django.db import connection

from datahub.interaction.models import Interaction, InteractionExportCountry

logger = getLogger(__name__)
cursor = connection.cursor()


def _get_export_country_interaction_with_discussed_countries():
    """
    Number of export country interactions with countries tagged
    where countries were discussed.
    """
    interactions = Interaction.objects.filter(
        were_countries_discussed=True,
    ).count()

    return interactions


def _get_all_export_interaction():
    """
    Number of interactions with countries tagged.
    """
    interactions = InteractionExportCountry.objects.count()

    return interactions


def _get_all_countries_with_a_company():
    """
    Number of all countries that had a company added.
    """
    countries = InteractionExportCountry.objects.all(
    ).select_related(
        'interaction',
    ).distinct('interaction__company_id').count()

    return countries


def _get_team_usage():
    """
    Count of all teams that used the new feature.
    """
    cursor.execute(
        """
        select count(1)
        from interaction_interaction ii
        inner join company_advisor ca on ii.created_by_id = ca.id
        inner join metadata_team mt on ca.dit_team_id = mt.id
        left join metadata_teamrole m on mt.role_id = m.id
        where ii.were_countries_discussed=true;
        """,
    )

    return cursor.fetchone()


def _get_top_5_team_usage():
    """
    Top 5 teams that used the new feature.
    """
    cursor.execute(
        """
        select mt.name "Team", m.name "Team type",
        count(*) "Number of interactions with export countries"
        from interaction_interaction ii
        inner join company_advisor ca on ii.created_by_id = ca.id
        inner join metadata_team mt on ca.dit_team_id = mt.id
        left join metadata_teamrole m on mt.role_id = m.id
        where ii.were_countries_discussed=true
        group by 1, 2
        order by "Number of interactions with export countries" desc
        limit 5;
        """,
    )

    return cursor.fetchone()


class Command(BaseCommand):
    """
    Command to query usage stats from the new interaction journey.
    """

    def handle(self, *args, **options):
        """
        Run the query and output the results as an info message to the log file.
        """
        interaction_usage_stats = """
        {result_1} uses of new interaction journey
        {result_2} countries added against {result_3}
        {result_4} teams used the new feature
        Top 5 users:
        {result_5}
        """.format(
            result_1=_get_export_country_interaction_with_discussed_countries(),
            result_2=_get_all_export_interaction(),
            result_3=_get_all_countries_with_a_company(),
            result_4=_get_team_usage()[0],
            result_5=_get_top_5_team_usage(),
        )
        logger.info(interaction_usage_stats)
