"""One off command to update LEPs to IDPs for Investment Projects."""

from datetime import datetime, timezone
from logging import getLogger

from django.core.management import BaseCommand

from datahub.investment.project.models import InvestmentProject

logger = getLogger(__name__)

delivery_partner_mappings = [
    # Cumbria LEP -> Cumbria
    {'lep': 'e96192bb-09f1-e511-8ffa-e4115bead28a', 'idp': '4d2d0351-ffaa-4a0d-986a-f13be4ec2198'},
    # Greater Manchester LEP -> Greater Manchester Combined Authority
    {'lep': '9abd575e-0af1-e511-8ffa-e4115bead28a', 'idp': '182e76ca-868d-4ca4-a336-17a26719f786'},
    # Liverpool City Region LEP -> Liverpool City Region Combined Authority
    {'lep': '87b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'dedd7553-63fe-41cc-874f-740d4cec8f97'},
    # Lancashire LEP -> Lancashire Combined Authority
    {'lep': '7db87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'c49e39af-fd14-49d6-ae34-aa9a4a9da65f'},
    # North East LEP -> North East Mayoral Combined Authority (NEMCA)
    {'lep': '6e85b4e3-0df1-e511-8ffa-e4115bead28a', 'idp': '58d8d795-fbb2-4ae5-aaa2-5c4415c78448'},
    # Tees Valley LEP -> Tees Valley Combined Authority (TVCA)
    {'lep': 'd5b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'b6e3d185-24ae-4b63-8c98-5717acf8e83e'},
    # Leeds City Region LEP -> West Yorkshire Combined Authority (WYCA)
    {'lep': '81b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '1de3306f-6550-4f3b-ad99-c6ed380ba527'},
    # Sheffield City Region LEP -> South Yorkshire Mayoral Combined Authority (SYMCA)
    {'lep': 'b7b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '33cb0c84-6d77-4aae-9931-1391b154b432'},
    # York and North Yorkshire LEP -> York and North Yorkshire Combined Authority (YNYCA)
    {'lep': 'edb87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '5b5846ae-805e-4e27-a2c7-ad03ae3a48c7'},
    # Hull & East Yorkshire LEP -> Hull & East Yorkshire
    {'lep': '67b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '881ebf0f-7e54-4dc2-a710-2592b8c2f3f3'},
    # Cheshire & Warrington LEP -> Cheshire & Warrington
    {'lep': '43b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'ef9520d0-4ac6-4afc-a7a5-f52a84d722cd'},
    # Coventry and Warwickshire LEP -> Coventry and Warwickshire
    {'lep': '47b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'fa7265d4-1b48-46f9-b1ad-4edb603a4b7a'},
    # Black Country LEP -> The Black Country
    {'lep': '9f457ec7-0df1-e511-8ffa-e4115bead28a', 'idp': '6bf47e48-720e-4774-9f54-25d03e42ab8c'},
    # Greater Birmingham and Solihull LEP -> Birmingham and Solihull
    {'lep': 'd722c64d-0af1-e511-8ffa-e4115bead28a', 'idp': 'bd5b1fc8-9f41-4f82-b01e-59b580405499'},
    # Worcestershire LEP -> Worcestershire
    {'lep': 'e9b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '8efff1df-cc61-4f50-a45f-8a86a39255b2'},
    # Greater Lincolnshire LEP -> Greater Lincolnshire
    {'lep': '5bb87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '7661d5c8-87cd-4f3d-a8d1-18537126d1d4'},
    # Derby, Derbyshire, Nottingham and Nottinghamshire (D2N2) LEP -> Derbyshire & Nottinghamshire
    {'lep': '9bd5dc7b-0bf1-e511-8ffa-e4115bead28a', 'idp': '42848f9f-5672-453c-b80c-dd234f5a22a0'},
    # Leicester and leicestershire LEP -> Leicester & Leicestershire
    {'lep': '83b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'c05199a7-7e71-44b2-9582-0a62bfa0a130'},
    # The Marches LEP -> Shropshire, Telford and Herefordshire
    {'lep': '2d11f1d5-0df1-e511-8ffa-e4115bead28a', 'idp': 'e3e4ba66-563d-41e9-af8a-eaf4ee4463b5'},
    # Stoke on Trent and Staffordshire LEP -> Stoke and Staffordshire
    {'lep': 'c9b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'e35991c5-45c2-426d-b5b9-18b5419d2582'},
    # Cornwall and Isles of Scilly LEP -> Cornwall and Isles of Scilly
    {'lep': '4e37faaa-09f1-e511-8ffa-e4115bead28a', 'idp': '02015c5c-4143-4b6b-b93e-36ab22d365fc'},
    # Dorset LEP -> Dorset
    {'lep': 'b8827a82-09f1-e511-8ffa-e4115bead28a', 'idp': 'b128bbd5-380c-4875-90fc-6c1551312943'},
    # West of England LEP -> West of England Combined Authority (WECA)
    {'lep': 'e3b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'e7d21909-338f-480e-838f-23a1c04b4885'},
    # GFirst LEP -> Gloucestershire
    {'lep': '688ea333-0af1-e511-8ffa-e4115bead28a', 'idp': '76b5619b-d08b-4527-a11a-850e1fc7eeff'},
    # Swindon & Wiltshire LEP -> Swindon & Wiltshire
    {'lep': 'd3b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'b5f4d2e3-07aa-46d2-bb96-f479f8de12ca'},
    # Coast to Capital LEP -> Sussex
    {'lep': '45b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '3ee9e0cb-136b-4b17-bb9e-ce6da411fc8a'},
    # Oxfordshire LEP -> Oxfordshire
    {'lep': 'adb87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'dde9feb4-1656-4363-ab9a-c41d1f92442d'},
    # Buckinghamshire LEP -> Buckinghamshire
    {'lep': '049b5f91-09f1-e511-8ffa-e4115bead28a', 'idp': 'ebd48659-e5b9-40a9-aa56-2051d4a0c78a'},
    # Berkshire LEP -> Berkshire
    {'lep': 'd9b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '0026f106-d6cc-4327-9d7a-d0951d3c9168'},
    # Hertfordshire LEP -> Hertfordshire
    {'lep': '63b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': '624ceb13-f970-45e8-9e9a-358445558bb0'},
    # Greater Cambridge and Greater Peterborough LEP -> Cambridge and Peterborough Combined Authority
    {'lep': '59b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'a557b7b7-8bf2-4c3d-9dbb-6d152b030fe3'},
    # New Anglia LEP -> Norfolk and Suffolk
    {'lep': 'cdcc392e-0bf1-e511-8ffa-e4115bead28a', 'idp': 'a8ef4192-8f14-4208-be99-bd4545d6eed6'},
    # South East Midlands LEP -> Northamptonshire, Bedforshire and Milton Keynes
    {'lep': 'c1b87bf6-9f1a-e511-8e8f-441ea13961e2', 'idp': 'ba97d018-c353-4232-b90d-f09af0f7cfc0'},
]


class Command(BaseCommand):
    """One off command to update LEPs to IDPs for Investment Projects.

    Update Local Enterprice Partner (LEP) to Investment Delivery Partner (IDP)
    for investment projects with an Actual land date values of 1st April 2024 onwards.
    """

    help = 'Update Local Enterprice Partner (LEP) to Investment Delivery Partner (IDP) for investment projects with an Actual land date values of 1st April 2024 onwards'

    log: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = {
            'projects': {'count': 0, 'errors': []},
            'leps': {'investment_project_count': 0, 'to_delete': 0, 'deleted': 0, 'errors': []},
            'idps': {'investment_project_count': 0, 'to_add': 0, 'added': 0, 'errors': []},
        }

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulate the command and only log expected changes without making changes.',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete LEPs that have a corresponding IDP.',
        )

    def handle(self, *args, **options):
        is_simulation = options['simulate']
        is_delete = options['delete']

        for delivery_partner_mapping in delivery_partner_mappings:
            projects = InvestmentProject.objects.filter(
                actual_land_date__gte=datetime(2024, 4, 1, tzinfo=timezone.utc),
                delivery_partners__in=[delivery_partner_mapping['lep']],
            ).prefetch_related('delivery_partners')
            self.log['leps']['investment_project_count'] += projects.count()
            for project in projects:
                project.delivery_partners.add(delivery_partner_mapping['idp'])
                self.log['idps']['to_add'] += 1
                if not is_simulation:
                    project.save()
                    self.log['idps']['added'] += 1

                if is_delete:
                    # Check new IDP is added
                    verify_project = InvestmentProject.objects.get(pk=project.id)
                    if verify_project.delivery_partners.filter(
                        pk=delivery_partner_mapping['idp'],
                    ).exists():
                        self.log['leps']['to_delete'] += 1
                        if not is_simulation:
                            project.delivery_partners.remove(delivery_partner_mapping['lep'])
                            project.save()
                            self.log['leps']['deleted'] += 1

        logger.info(self.log)
