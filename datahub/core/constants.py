from collections import namedtuple
from enum import Enum

Constant = namedtuple('Constant', ('name', 'id'))
OrderedConstant = namedtuple('OrderedConstant', ('name', 'id', 'order'))
AdministrativeAreaConstant = namedtuple(
    'AdministrativeAreaConstant',
    (
        'name',
        'id',
        'area_code',
        'country_id',
    ),
)


class Country(Enum):
    """Countries."""

    anguilla = Constant('Anguilla', '995f66a0-5d95-e211-a939-e4115bead28a')
    argentina = Constant('Argentina', '9c5f66a0-5d95-e211-a939-e4115bead28a')
    azerbaijan = Constant('Azerbaijan', 'a15f66a0-5d95-e211-a939-e4115bead28a')
    canada = Constant('Canada', '5daf72a6-5d95-e211-a939-e4115bead28a')
    cayman_islands = Constant('Cayman Islands', '5faf72a6-5d95-e211-a939-e4115bead28a')
    france = Constant('France', '82756b9a-5d95-e211-a939-e4115bead28a')
    greece = Constant('Greece', 'e3f682ac-5d95-e211-a939-e4115bead28a')
    ireland = Constant('Ireland', '736a9ab2-5d95-e211-a939-e4115bead28a')
    isle_of_man = Constant('Isle of Man', '79756b9a-5d95-e211-a939-e4115bead28a')
    italy = Constant('Italy', '84756b9a-5d95-e211-a939-e4115bead28a')
    japan = Constant('Japan', '85756b9a-5d95-e211-a939-e4115bead28a')
    montserrat = Constant('Montserrat', '1350bdb8-5d95-e211-a939-e4115bead28a')
    united_kingdom = Constant('United Kingdom', '80756b9a-5d95-e211-a939-e4115bead28a')
    united_states = Constant('United States', '81756b9a-5d95-e211-a939-e4115bead28a')


class AdministrativeArea(Enum):
    """Administrative Areas"""

    # United States
    alabama = AdministrativeAreaConstant(
        'Alabama',
        '8ad3f33a-ace8-40ec-bd2c-638fdc3024ea',
        'AL',
        Country.united_states.value.id,
    )
    new_york = AdministrativeAreaConstant(
        'New York',
        'aa65b701-244a-41fc-bd31-0a546303106a',
        'NY',
        Country.united_states.value.id,
    )
    texas = AdministrativeAreaConstant(
        'Texas',
        'c35c119a-bc4d-4e48-9ace-167dbe8cb695',
        'TX',
        Country.united_states.value.id,
    )


class SectorCluster(Enum):
    """Sector clusters."""

    creative_lifestyle_and_learning = Constant(
        'Creative, Lifestyle and Learning',
        'ed3671b5-d194-4ee3-9bbf-a04773711dd9',
    )
    defence_and_security = Constant(
        'Defence and Security',
        '7cdae131-6fc4-4c4c-a977-07f5be64a1c4',
    )
    energy_and_infrastructure = Constant(
        'Energy & Infrastructure',
        'c79ec2c9-9b31-45a0-9d32-b5cc284dc8d1',
    )
    financial_and_professional_services = Constant(
        'Financial & Professional Services',
        '7be7a38f-1a77-44bf-abee-3049ba50a6a8',
    )
    healthcare_life_sciences_and_bio_economy = Constant(
        'Healthcare, Life Sciences and Bio-Economy',
        '0804745e-80b6-4bd1-8101-30e7a431623e',
    )
    technology_entrepreneurship_and_advanced_manufacturing = Constant(
        'Technology, Entrepreneurship and Advanced Manufacturing',
        '531d3510-3f42-41fd-86b5-fa686fdfe33f',
    )


class Sector(Enum):
    """Sectors (not all of them!)."""

    aerospace_assembly_aircraft = Constant(
        'Aerospace : Manufacturing and Assembly : Aircraft',
        'b422c9d2-5f95-e211-a939-e4115bead28a',
    )
    renewable_energy_wind = Constant(
        'Renewable Energy : Wind',
        'a4959812-6095-e211-a939-e4115bead28a',
    )


class Title(Enum):
    """Titles."""

    admiral = Constant('Admiral', 'c1d9b924-6095-e211-a939-e4115bead28a')
    admiral_of_the_fleet = Constant('Admiral of the Fleet', 'c2d9b924-6095-e211-a939-e4115bead28a')
    air_chief_marshal = Constant('Air Chief Marshal', 'c3d9b924-6095-e211-a939-e4115bead28a')
    air_commodore = Constant('Air Commodore', 'c4d9b924-6095-e211-a939-e4115bead28a')
    air_marshal = Constant('Air Marshal', 'c5d9b924-6095-e211-a939-e4115bead28a')
    air_vice_marshal = Constant('Air Vice-Marshal', 'c6d9b924-6095-e211-a939-e4115bead28a')
    baroness = Constant('Baroness', 'bed9b924-6095-e211-a939-e4115bead28a')
    brigadier = Constant('Brigadier', 'c7d9b924-6095-e211-a939-e4115bead28a')
    captain = Constant('Captain', 'c8d9b924-6095-e211-a939-e4115bead28a')
    colonel = Constant('Colonel', 'c9d9b924-6095-e211-a939-e4115bead28a')
    commander = Constant('Commander', 'cad9b924-6095-e211-a939-e4115bead28a')
    commodore = Constant('Commodore', 'cbd9b924-6095-e211-a939-e4115bead28a')
    corporal = Constant('Corporal', 'f4c5716b-1770-e411-a72b-e4115bead28a')
    dame = Constant('Dame', 'bad9b924-6095-e211-a939-e4115bead28a')
    dr = Constant('Dr', 'b5d9b924-6095-e211-a939-e4115bead28a')
    field_marshal = Constant('Field Marshal', 'ccd9b924-6095-e211-a939-e4115bead28a')
    flight_lieutenant = Constant('Flight Lieutenant', 'cdd9b924-6095-e211-a939-e4115bead28a')
    flying_officer = Constant('Flying Officer', 'ced9b924-6095-e211-a939-e4115bead28a')
    general = Constant('General', 'cfd9b924-6095-e211-a939-e4115bead28a')
    group_captain = Constant('Group Captain', 'd0d9b924-6095-e211-a939-e4115bead28a')
    he = Constant('HE', 'bfd9b924-6095-e211-a939-e4115bead28a')
    hrh = Constant('HRH', 'c0d9b924-6095-e211-a939-e4115bead28a')
    lady = Constant('Lady', 'b8d9b924-6095-e211-a939-e4115bead28a')
    lieutenant = Constant('Lieutenant', 'd1d9b924-6095-e211-a939-e4115bead28a')
    lieutenant_colonel = Constant('Lieutenant Colonel', 'd3d9b924-6095-e211-a939-e4115bead28a')
    lieutenant_commander = Constant('Lieutenant Commander', 'd2d9b924-6095-e211-a939-e4115bead28a')
    lieutenant_general = Constant('Lieutenant General', 'd4d9b924-6095-e211-a939-e4115bead28a')
    lord = Constant('Lord', 'b9d9b924-6095-e211-a939-e4115bead28a')
    major = Constant('Major', 'd5d9b924-6095-e211-a939-e4115bead28a')
    major_general = Constant('Major General', 'd6d9b924-6095-e211-a939-e4115bead28a')
    marshal_of_the_raf = Constant('Marshal of the RAF', 'd7d9b924-6095-e211-a939-e4115bead28a')
    miss = Constant('Miss', 'a46cb21e-6095-e211-a939-e4115bead28a')
    mr = Constant('Mr', 'a26cb21e-6095-e211-a939-e4115bead28a')
    mrs = Constant('Mrs', 'a36cb21e-6095-e211-a939-e4115bead28a')
    ms = Constant('Ms', 'b4d9b924-6095-e211-a939-e4115bead28a')
    pilot_officer = Constant('Pilot Officer', 'd8d9b924-6095-e211-a939-e4115bead28a')
    professor = Constant('Professor', 'bbd9b924-6095-e211-a939-e4115bead28a')
    rear_admiral = Constant('Rear Admiral', 'd9d9b924-6095-e211-a939-e4115bead28a')
    reverend = Constant('Reverend', 'b6d9b924-6095-e211-a939-e4115bead28a')
    second_lieutenant = Constant('Second Lieutenant', 'dad9b924-6095-e211-a939-e4115bead28a')
    sir = Constant('Sir', 'b7d9b924-6095-e211-a939-e4115bead28a')
    squadron_leader = Constant('Squadron Leader', 'dbd9b924-6095-e211-a939-e4115bead28a')
    sub_lieutenant = Constant('Sub-Lieutenant', '744cd12a-6095-e211-a939-e4115bead28a')
    the_hon = Constant('The Hon', 'bcd9b924-6095-e211-a939-e4115bead28a')
    the_rt_hon = Constant('The Rt Hon', 'bdd9b924-6095-e211-a939-e4115bead28a')
    vice_admiral = Constant('Vice Admiral', '754cd12a-6095-e211-a939-e4115bead28a')
    wing_commander = Constant('Wing Commander', '764cd12a-6095-e211-a939-e4115bead28a')


class UKRegion(Enum):
    """UK Regions."""

    alderney = Constant('Alderney', '934cd12a-6095-e211-a939-e4115bead28a')
    all = Constant('All', '1718e330-6095-e211-a939-e4115bead28a')
    channel_islands = Constant('Channel Islands', '8b4cd12a-6095-e211-a939-e4115bead28a')
    east_midlands = Constant('East Midlands', '844cd12a-6095-e211-a939-e4115bead28a')
    east_of_england = Constant('East of England', '864cd12a-6095-e211-a939-e4115bead28a')
    england = Constant('England', '8a4cd12a-6095-e211-a939-e4115bead28a')
    fdi_hub = Constant('FDI Hub', '804cd12a-6095-e211-a939-e4115bead28a')
    guernsey = Constant('Guernsey', '904cd12a-6095-e211-a939-e4115bead28a')
    isle_of_man = Constant('Isle of Man', '8f4cd12a-6095-e211-a939-e4115bead28a')
    jersey = Constant('Jersey', '924cd12a-6095-e211-a939-e4115bead28a')
    london = Constant('London', '874cd12a-6095-e211-a939-e4115bead28a')
    north_east = Constant('North East', '814cd12a-6095-e211-a939-e4115bead28a')
    northern_ireland = Constant('Northern Ireland', '8e4cd12a-6095-e211-a939-e4115bead28a')
    north_west = Constant('North West', '824cd12a-6095-e211-a939-e4115bead28a')
    sark = Constant('Sark', '914cd12a-6095-e211-a939-e4115bead28a')
    scotland = Constant('Scotland', '8c4cd12a-6095-e211-a939-e4115bead28a')
    south_east = Constant('South East', '884cd12a-6095-e211-a939-e4115bead28a')
    south_west = Constant('South West', '894cd12a-6095-e211-a939-e4115bead28a')
    ukti_dubai_hub = Constant('UKTI Dubai Hub', 'e1dd40e9-3dfd-e311-8a2b-e4115bead28a')
    wales = Constant('Wales', '8d4cd12a-6095-e211-a939-e4115bead28a')
    west_midlands = Constant('West Midlands', '854cd12a-6095-e211-a939-e4115bead28a')
    yorkshire_and_the_humber = Constant(
        'Yorkshire and The Humber', '834cd12a-6095-e211-a939-e4115bead28a',
    )


class Service(Enum):
    """Service."""

    enquiry_or_referral_received = Constant(
        'Enquiry or Referral Received',
        'fee6779d-e127-4e1e-89f6-d614b4df3581',
    )

    inbound_referral = Constant(
        'Enquiry or Referral Received : Other Inbound Export Referral',
        '9984b82b-3499-e211-a939-e4115bead28a',
    )
    account_management = Constant(
        'Account Management : General',
        '9484b82b-3499-e211-a939-e4115bead28a',
    )

    providing_investment_advice_and_information = Constant(
        'Providing Investment Advice & Information',
        'ef3218c1-bed6-4ad8-b8d5-8af2430d32ff',
    )
    making_export_introductions = Constant(
        'Making Export Introductions',
        '1477622e-9adb-4017-8d8d-fe3221f1d2fc',
    )

    investment_enquiry_requested_more_information = Constant(
        'Investment Enquiry – Requested more information from source (IST use only)',
        '73ceedc1-c139-4bdf-9e47-17b1bae488da',
    )
    investment_enquiry_confirmed_prospect = Constant(
        'Investment Enquiry – Confirmed prospect project status (IST use only)',
        '4f142041-2b9d-4776-ace8-22612260eae6',
    )
    investment_enquiry_assigned_to_ist_sas = Constant(
        'Investment Enquiry – Assigned to IST-SAS (IST use only)',
        'c579b89b-d49d-4926-a6a4-0a1459cd25cb',
    )
    investment_enquiry_assigned_to_ist_cmc = Constant(
        'Investment Enquiry – Assigned to IST-CMC (IST use only)',
        '2591b204-8a31-4824-a93b-d7a03dca8cb5',
    )
    investment_enquiry_assigned_to_hq = Constant(
        'Investment Enquiry – Assigned to HQ (IST use only)',
        '38a67092-f485-4ea1-8a1a-402b949d2d13',
    )
    investment_enquiry_transferred_to_lep = Constant(
        'Investment Enquiry – Transferred to LEP (IST use only)',
        '48e6bc3e-56c5-4bdc-a718-093614547d73',
    )
    investment_enquiry_transferred_to_da = Constant(
        'Investment Enquiry – Transferred to DA (IST use only)',
        '05c8175a-abf5-4cc6-af34-bcee8699fd4b',
    )
    investment_enquiry_transferred_to_lp = Constant(
        'Investment Enquiry – Transferred to L&P (IST use only)',
        'c707f81d-ae66-490a-98f5-575438944c43',
    )
    investment_ist_aftercare_offered = Constant(
        'Investment - IST Aftercare Offered (IST use only)',
        '79824229-fd87-483f-b929-8f2b9531492b',
    )


class Team(Enum):
    """Team."""

    healthcare_uk = Constant('Healthcare UK', '3ff47a07-002c-e311-a78e-e4115bead28a')
    tees_valley_lep = Constant('Tees Valley LEP', 'a889ef76-8925-e511-b6bc-e4115bead28a')
    td_events_healthcare = Constant(
        'TD - Events - Healthcare', 'daf924aa-9698-e211-a939-e4115bead28a',
    )
    food_from_britain = Constant('Food From Britain', '8cf924aa-9698-e211-a939-e4115bead28a')
    crm = Constant('crm', 'a7f924aa-9698-e211-a939-e4115bead28a')


class HeadquarterType(Enum):
    """Headquarter type."""

    ukhq = Constant('ukhq', '3e6debb4-1596-40c5-aa25-f00da0e05af9')
    ehq = Constant('ehq', 'eb59eaeb-eeb8-4f54-9506-a5e08773046b')
    ghq = Constant('ghq', '43281c5e-92a4-4794-867b-b4d5f801e6f3')


class EmployeeRange(Enum):
    """Employee range constants."""

    range_1_to_9 = Constant('1 to 9', '3dafd8d0-5d95-e211-a939-e4115bead28a')
    range_10_to_49 = Constant('10 to 49', '3eafd8d0-5d95-e211-a939-e4115bead28a')
    range_50_to_249 = Constant('50 to 249', '3fafd8d0-5d95-e211-a939-e4115bead28a')
    range_250_to_499 = Constant('250 to 499', '40afd8d0-5d95-e211-a939-e4115bead28a')
    range_500_plus = Constant('500+', '41afd8d0-5d95-e211-a939-e4115bead28a')


class TurnoverRange(Enum):
    """Turnover range constants."""

    range_0_to_1_34 = Constant('£0 ti £1.34M', '774cd12a-6095-e211-a939-e4115bead28a')
    range_1_34_to_6_7 = Constant('£1.34 to £6.7M', '784cd12a-6095-e211-a939-e4115bead28a')
    range_6_7_to_33_5 = Constant('£6.7 to £33.5M', '794cd12a-6095-e211-a939-e4115bead28a')
    range_33_5_plus = Constant('£33.5M+', '7a4cd12a-6095-e211-a939-e4115bead28a')


class InvestmentProjectStage(Enum):
    """Investment project stage constants."""

    prospect = OrderedConstant(
        'Prospect', '8a320cc9-ae2e-443e-9d26-2f36452c2ced', 200.0,
    )
    assign_pm = OrderedConstant(
        'Assign PM', 'c9864359-fb1a-4646-a4c1-97d10189fc03', 300.0,
    )
    active = OrderedConstant(
        'Active', '7606cc19-20da-4b74-aba1-2cec0d753ad8', 400.0,
    )
    verify_win = OrderedConstant(
        'Verify win', '49b8f6f3-0c50-4150-a965-2c974f3149e3', 500.0,
    )
    won = OrderedConstant('Won', '945ea6d1-eee3-4f5b-9144-84a75b71b8e6', 600.0)

    @classmethod
    def get_by_id(cls, item_id):
        """Gets the corresponding item for a given id."""
        return next(
            (item for item in cls if str(item.value.id) == str(item_id)),
            None,
        )


class InvestmentType(Enum):
    """Investment type constants."""

    fdi = Constant('FDI', '3e143372-496c-4d1e-8278-6fdd3da9b48b')
    non_fdi = Constant('Non-FDI', '9c364e64-2b28-401b-b2df-50e08b0bca44')
    commitment_to_invest = Constant(
        'Commitment to invest',
        '031269ab-b7ec-40e9-8a4e-7371404f0622',
    )


class ReferralSourceActivity(Enum):
    """Referral source activity constants."""

    cold_call = Constant(
        'Cold call', '0c4f8e74-d34f-4aca-b764-a44cdc2d0087',
    )
    direct_enquiry = Constant(
        'Direct enquiry', '7d98f3a6-3e3f-40ac-a6f3-3f0c251ec1d2',
    )
    event = Constant(
        'Event', '3816a95b-6a76-4ad0-8ae9-b0d7e7d2b79c',
    )
    marketing = Constant(
        'Marketing', '0acf0e68-e09e-4e5d-92b6-e72e5a5c7ea4',
    )
    multiplier = Constant(
        'Multiplier', 'e95cddb3-9407-4c8a-b5a6-2616117b0aae',
    )
    none = Constant(
        'None', 'aba8f653-264f-48d8-950e-07f9c418c7b0',
    )
    other = Constant(
        'Other', '318e6e9e-2a0e-4e4b-a495-c48aeee4b996',
    )
    relationship_management_activity = Constant(
        'Relationship management activity',
        '668e999c-a669-4d9b-bfbf-6275ceed86da',
    )
    personal_reference = Constant(
        'Personal reference', 'c03c4043-18b4-4463-a36b-a1af1b35f95d',
    )
    website = Constant(
        'Website', '812b2f62-fe62-4cc8-b69c-58f3e2ebac17',
    )


class InvestmentBusinessActivity(Enum):
    """Investment business activity constants."""

    sales = Constant('Sales', '71946309-c92c-4c5b-9c42-8502cc74c72e')
    retail = Constant('Retail', 'a2dbd807-ae52-421c-8d1d-88adfc7a506b')
    other = Constant('Other', 'befab707-5abd-4f47-8477-57f091e6dac9')


class FDIType(Enum):
    """Investment FDI type constants."""

    creation_of_new_site_or_activity = Constant(
        'Creation of new site or activity',
        'f8447013-cfdc-4f35-a146-6619665388b3',
    )


class FDIValue(Enum):
    """Investment FDI value constants."""

    higher = Constant(
        'Higher', '38e36c77-61ad-4186-a7a8-ac6a1a1104c6',
    )


class SalaryRange(Enum):
    """Average salary constants."""

    below_25000 = OrderedConstant(
        'Below £25,000', '2943bf3d-32dd-43be-8ad4-969b006dee7b', 100.0,
    )


class InvestmentStrategicDriver(Enum):
    """Investment strategic driver constants."""

    access_to_market = Constant(
        'Access to market', '382aa6d1-a362-4166-a09d-f579d9f3be75',
    )


class ExportSegment(Enum):
    """ExportSegment type constants."""

    hep = Constant('hep', 'High export potential')
    non_hep = Constant('non-hep', 'Not high export potential')


class ExportSubSegment(Enum):
    """ExportSubSegment type constants."""

    sustain_nurture_and_grow = Constant(
        'sustain_nurture_and_grow',
        'Sustain: nurture & grow',
    )
    sustain_develop_export_capability = Constant(
        'sustain_develop_export_capability',
        'Sustain: develop export capability',
    )
    sustain_communicate_benefits = Constant(
        'sustain_communicate_benefits',
        'Sustain: communicate benefits',
    )
    sustain_increase_competitiveness = Constant(
        'sustain_increase_competitiveness',
        'Sustain: increase competitiveness',
    )
    reassure_nurture_and_grow = Constant(
        'reassure_nurture_and_grow',
        'Reassure: nurture & grow',
    )
    reassure_develop_export_capability = Constant(
        'reassure_develop_export_capability',
        'Reassure: develop export capability',
    )
    reassure_leave_be = Constant(
        'reassure_leave_be',
        'Reassure: leave be',
    )
    reassure_change_the_game = Constant(
        'reassure_change_the_game',
        'Reassure: change the game',
    )
    promote_develop_export_capability = Constant(
        'promote_develop_export_capability',
        'Promote: develop export capability',
    )
    promote_communicate_benefits = Constant(
        'promote_communicate_benefits',
        'Promote: communicate benefits',
    )
    promote_change_the_game = Constant(
        'promote_change_the_game',
        'Promote: change the game',
    )
    challenge = Constant('challenge', 'Challenge')
