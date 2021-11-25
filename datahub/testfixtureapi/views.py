import json
import logging
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, schema
from rest_framework.response import Response

from datahub.company.models import (
    Advisor,
    Company,
    Contact,
    OneListCoreTeamMember,
)
from datahub.company_referral.models import CompanyReferral
from datahub.event.models import Event
from datahub.feature_flag.models import FeatureFlag
from datahub.interaction.models import Interaction, InteractionDITParticipant
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.investment.project.models import (
    InvestmentProject,
    InvestmentProjectStageLog,
    InvestmentProjectTeamMember,
)
from datahub.investment.project.proposition.models import Proposition
from datahub.oauth.cache import add_token_data_to_cache

logger = logging.getLogger(__name__)

E2E_FIXTURE_DIR = settings.ROOT_DIR('fixtures/test_data.yaml')
TEST_USER_TOKEN_TIMEOUT = 24 * 3600


@api_view(['POST'])
@authentication_classes(())
@permission_classes(())
@schema(None)
def reset_fixtures(request):
    """
    Reset db to a known state.

    This view is to facilitate End to End testing. It has no authentication and should
    only be enabled to run tests and never in production!

    The database will have its objects (except Metadata) removed and reset to the state in the
    fixtures file.
    """
    if not settings.ALLOW_TEST_FIXTURE_SETUP:
        logger.warning(
            'The `reset_fixture` endpoint is not enabled. The ALLOW_TEST_FIXTURE_SETUP environment'
            ' variable is not set.',
        )
        raise Http404

    with transaction.atomic():
        LargeCapitalInvestorProfile.objects.all().delete()
        LargeCapitalOpportunity.objects.all().delete()
        InvestmentProject.objects.all().delete()
        InvestmentProjectStageLog.objects.all().delete()
        InvestmentProjectTeamMember.objects.all().delete()
        Proposition.objects.all().delete()
        InteractionDITParticipant.objects.all().delete()
        Event.objects.all().delete()
        FeatureFlag.objects.all().delete()
        Advisor.objects.all().delete()
        Company.objects.all().delete()
        Contact.objects.all().delete()
        CompanyReferral.objects.all().delete()
        Interaction.objects.all().delete()
        OneListCoreTeamMember.objects.all().delete()

    call_command('loaddata', str(E2E_FIXTURE_DIR))

    logger.info('Reset fixtures completed.')

    return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes(())
@permission_classes(())
@schema(None)
def create_user(request):
    """
    Create user

    This view is to facilitate End to End testing. It has no authentication and should
    only be enabled to run tests and never in production!

    POST to this view with a payload which is a single JSON object containing the following
    properties:

    {
        "first_name": <first name>,
        "last_name": <last name>,
        "email": <email>,
        "dit_team_id: <DIT team id>,
        "sso_email_user_id": <sso email user id>,
        "token": <desired token>
    }

    Provided token can be used to authenticate subsequent user requests.
    """
    if not settings.ALLOW_TEST_FIXTURE_SETUP:
        logger.warning(
            'The `create_user` endpoint is not enabled. The ALLOW_TEST_FIXTURE_SETUP environment'
            ' variable is not set.',
        )
        raise Http404

    seed_user_data = {
        'first_name': request.data['first_name'],
        'last_name': request.data['last_name'],
        'email': request.data['email'],
        'dit_team_id': request.data['dit_team_id'],
        'sso_email_user_id': request.data['sso_email_user_id'],
    }

    user_info = json.dumps(seed_user_data, indent=4, sort_keys=True)
    logger.info(f'Creating a user: {user_info}')

    seed_user = Advisor.objects.create(**seed_user_data)

    token = request.data['token']
    add_token_data_to_cache(
        token,
        seed_user.email,
        seed_user.sso_email_user_id,
        TEST_USER_TOKEN_TIMEOUT,
    )
    logger.info(f'Created a token `{token}` for user {seed_user.id}.')

    return Response(status=status.HTTP_201_CREATED, data={'id': seed_user.id})


@api_view(['POST'])
@authentication_classes(())
@permission_classes(())
@schema(None)
def load_fixture(request):
    """
    Load fixture endpoint.

    This view is to facilitate End to End testing. It has no authentication and should
    only be enabled to run tests and never in production!

    The fixture should be in a JSON format, e.g.:

    {
        "fixture": [
            {
                "model": "company.advisor",
                "pk": "413a608e-84a4-11e6-ea22-56b6b6499622",
                "fields":
                {
                    "email": "abc@def",
                    "first_name": "First name",
                    "last_name": "Last name",
                    "dit_team": "162a3959-9798-e211-a939-e4115bead28a"
                }
            }
        ]
    }

    """
    if not settings.ALLOW_TEST_FIXTURE_SETUP:
        logger.warning(
            'The `load_fixture` endpoint is not enabled. The ALLOW_TEST_FIXTURE_SETUP environment'
            ' variable is not set.',
        )
        raise Http404

    fixture = request.data['fixture']

    fixture_info = json.dumps(fixture, indent=4, sort_keys=True)
    logger.info(f'Loading fixture: {fixture_info}')

    with NamedTemporaryFile(suffix='.json') as tmp_file:
        tmp_file.write(json.dumps(fixture).encode())
        tmp_file.seek(0)

        call_command('loaddata', tmp_file.name)

    return Response(status=status.HTTP_201_CREATED)
