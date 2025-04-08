"""One off command to update LEPs to IDPs for Investment Projects."""

from datetime import datetime, timezone
from logging import getLogger

from django.core.management import BaseCommand

from datahub.investment.project.models import InvestmentProject

logger = getLogger(__name__)

delivery_partner_mappings = [
    {"lep": "e96192bb-09f1-e511-8ffa-e4115bead28a",
        "idp": "4d2d0351-ffaa-4a0d-986a-f13be4ec2198"},
    {"lep": "9abd575e-0af1-e511-8ffa-e4115bead28a",
        "idp": "182e76ca-868d-4ca4-a336-17a26719f786"},
    {"lep": "87b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "dedd7553-63fe-41cc-874f-740d4cec8f97"},
    {"lep": "7db87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "c49e39af-fd14-49d6-ae34-aa9a4a9da65f"},
    {"lep": "6e85b4e3-0df1-e511-8ffa-e4115bead28a",
        "idp": "58d8d795-fbb2-4ae5-aaa2-5c4415c78448"},
    {"lep": "d5b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "b6e3d185-24ae-4b63-8c98-5717acf8e83e"},
    {"lep": "81b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "1de3306f-6550-4f3b-ad99-c6ed380ba527"},
    {"lep": "b7b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "33cb0c84-6d77-4aae-9931-1391b154b432"},
    {"lep": "edb87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "5b5846ae-805e-4e27-a2c7-ad03ae3a48c7"},
    {"lep": "67b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "881ebf0f-7e54-4dc2-a710-2592b8c2f3f3"},
    {"lep": "43b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "ef9520d0-4ac6-4afc-a7a5-f52a84d722cd"},
    {"lep": "47b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "fa7265d4-1b48-46f9-b1ad-4edb603a4b7a"},
    {"lep": "9f457ec7-0df1-e511-8ffa-e4115bead28a",
        "idp": "6bf47e48-720e-4774-9f54-25d03e42ab8c"},
    {"lep": "e9b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "8efff1df-cc61-4f50-a45f-8a86a39255b2"},
    {"lep": "83b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "c05199a7-7e71-44b2-9582-0a62bfa0a130"},
    {"lep": "2d11f1d5-0df1-e511-8ffa-e4115bead28a",
        "idp": "e3e4ba66-563d-41e9-af8a-eaf4ee4463b5"},
    {"lep": "c9b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "e35991c5-45c2-426d-b5b9-18b5419d2582"},
    {"lep": "4e37faaa-09f1-e511-8ffa-e4115bead28a",
        "idp": "02015c5c-4143-4b6b-b93e-36ab22d365fc"},
    {"lep": "b8827a82-09f1-e511-8ffa-e4115bead28a",
        "idp": "b128bbd5-380c-4875-90fc-6c1551312943"},
    {"lep": "e3b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "e7d21909-338f-480e-838f-23a1c04b4885"},
    {"lep": "688ea333-0af1-e511-8ffa-e4115bead28a",
        "idp": "76b5619b-d08b-4527-a11a-850e1fc7eeff"},
    {"lep": "d3b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "b5f4d2e3-07aa-46d2-bb96-f479f8de12ca"},
    {"lep": "adb87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "dde9feb4-1656-4363-ab9a-c41d1f92442d"},
    {"lep": "049b5f91-09f1-e511-8ffa-e4115bead28a",
        "idp": "ebd48659-e5b9-40a9-aa56-2051d4a0c78a"},
    {"lep": "d9b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "0026f106-d6cc-4327-9d7a-d0951d3c9168"},
    {"lep": "63b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "624ceb13-f970-45e8-9e9a-358445558bb0"},
    {"lep": "59b87bf6-9f1a-e511-8e8f-441ea13961e2",
        "idp": "a557b7b7-8bf2-4c3d-9dbb-6d152b030fe3"},
    {"lep": "cdcc392e-0bf1-e511-8ffa-e4115bead28a",
        "idp": "a8ef4192-8f14-4208-be99-bd4545d6eed6"},
]


class Command(BaseCommand):
    """One off command to update LEPs to IDPs for Investment Projects.

    Update Local Enterprice Partner (LEP) to Investment Delivery Partner (IDP)
    for investment projects with an Actual land date values of 1st April 2024 onwards.
    """

    help = 'Update Local Enterprice Partner (LEP) to Investment Delivery Partner (IDP) for investment projects with an Actual land date values of 1st April 2024 onwards'

    def handle(self, *args, **options):
        leps = [delivery_partner['lep']
                for delivery_partner in delivery_partner_mappings]

        projects = InvestmentProject.objects.filter(
            actual_land_date__gte=datetime(2024, 4, 1, tzinfo=timezone.utc),
            delivery_partners__in=leps,
        ).prefetch_related('delivery_partners')

        details = [
            {
                'id': project.id,
                'name': project.name,
                'delivery_partners': [{'id': delivery_partner.id, 'name': delivery_partner.name} for delivery_partner in project.delivery_partners.all()],
            }
            for project in projects
        ]

        logger.info(details)

# list(map(lambda: details: logger.info(score_list.name), score_list))

        for dpm in delivery_partner_mappings:
            logger.info(dpm)
            projects = InvestmentProject.objects.filter(
                actual_land_date__gte=datetime(
                    2024, 4, 1, tzinfo=timezone.utc),
                delivery_partners__in=[dpm['lep']],
            ).prefetch_related('delivery_partners')
            logger.info(projects.count())
            for project in projects:
                project.delivery_partners.add(dpm['idp'])
                project.save()
                # Check new IDP is added
                logger.info(project.__dict__)
                logger.info(project.id)
                verify_project = InvestmentProject.objects.get(
                    pk=project.id)
                logger.info(dpm['idp'])
                logger.info(list(verify_project.delivery_partners.all()))
                if verify_project.delivery_partners.filter(pk=dpm['idp']).exists():
                    logger.info(f'>>>>>>>>>> > Removing ${dpm["lep"]}')
                    project.delivery_partners.remove(dpm['lep'])
                    project.save()


# If added remove existing LEP.
