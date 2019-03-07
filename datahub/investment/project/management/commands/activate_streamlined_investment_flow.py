import reversion
from django.core.management.base import BaseCommand

from datahub.core.constants import InvestmentProjectStage
from datahub.feature_flag.models import FeatureFlag
from datahub.investment.project.constants import FEATURE_FLAG_STREAMLINED_FLOW
from datahub.investment.project.models import InvestmentProject


FEATURE_DESCRIPTION = (
    'The removal of the Assign PM stage from investment flow to '
    'streamline the process of completing an investment project.'
)


class Command(BaseCommand):
    """
    Command to activate the streamlined investment flow feature and move all projects
    that have a status of Assign PM back to the Prospect stage.
    """

    help = ('Activates the streamlined investment flow and update all '
            'projects currently at the Assign PM stage')

    def activate_streamlined_investment_flow_feature(self):
        """
        Activate the streamlined investment flow feature and creating the feature
        flag if not already present.
        """
        FeatureFlag.objects.update_or_create(
            code=FEATURE_FLAG_STREAMLINED_FLOW,
            defaults={'description': FEATURE_DESCRIPTION, 'is_active': True},
        )
        self.stdout.write(self.style.SUCCESS('Activated streamlined investment flow'))

    def move_assign_pm_investment_projects_back_to_prospect(self):
        """
        Move projects at the Assign PM stage back to Prospect.
        Save each project individually to unsure search is updated and
        to create an audit of the change.
        """
        projects = InvestmentProject.objects.filter(
            stage_id=InvestmentProjectStage.assign_pm.value.id,
        )
        for project in projects.iterator():
            with reversion.create_revision():
                project.stage_id = InvestmentProjectStage.prospect.value.id
                project.save()
                reversion.set_comment('Moved project stage from Assign PM back to Prospect')
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {projects.count()} projects from Assign PM to Prospect',
            ),
        )

    def handle(self, *args, **options):
        """
        Move projects from Assign PM stage back to Prospect.
        Activate streamlined investment flow feature.

        """
        self.move_assign_pm_investment_projects_back_to_prospect()
        self.activate_streamlined_investment_flow_feature()
