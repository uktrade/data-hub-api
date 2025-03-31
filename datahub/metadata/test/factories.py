from random import randrange, sample

import factory

from datahub.core import constants
from datahub.metadata.models import Service


class ServiceFactory(factory.django.DjangoModelFactory):
    """Service factory."""

    segment = factory.Sequence(lambda n: f'name {n}')

    contexts = factory.LazyFunction(
        lambda: sample(
            Service.Context.values,
            randrange(0, len(Service.Context.values)),
        ),
    )

    class Meta:
        model = 'metadata.Service'


class ChildServiceFactory(factory.django.DjangoModelFactory):
    """Child service factory."""

    segment = factory.Sequence(lambda n: f'child name {n}')
    parent = factory.SubFactory(ServiceFactory)
    contexts = factory.LazyFunction(
        lambda: sample(
            Service.Context.values,
            randrange(0, len(Service.Context.values)),
        ),
    )

    class Meta:
        model = 'metadata.Service'


class TeamRoleFactory(factory.django.DjangoModelFactory):
    """TeamRole factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.TeamRole'


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory."""

    name = factory.Sequence(lambda n: f'name {n}')
    role = factory.SubFactory(TeamRoleFactory)
    uk_region_id = constants.UKRegion.east_midlands.value.id
    country_id = constants.Country.france.value.id
    tags = []

    class Meta:
        model = 'metadata.Team'


class ReferralSourceActivityFactory(factory.django.DjangoModelFactory):
    """ReferralSourceActivity factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceActivity'


class ReferralSourceWebsiteFactory(factory.django.DjangoModelFactory):
    """ReferralSourceWebsite factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceWebsite'


class ReferralSourceMarketingFactory(factory.django.DjangoModelFactory):
    """ReferralSourceMarketing factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceMarketing'


class SectorClusterFactory(factory.django.DjangoModelFactory):
    """SectorCluster factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.SectorCluster'


class SectorFactory(factory.django.DjangoModelFactory):
    """Sector factory."""

    segment = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.Sector'


class CountryFactory(factory.django.DjangoModelFactory):
    """Country factory."""

    class Meta:
        model = 'metadata.Country'


class AdministrativeAreasFactory(factory.django.DjangoModelFactory):
    """Administrative Area factory."""

    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = 'metadata.AdministrativeArea'


class PostcodeDataFactory(factory.django.DjangoModelFactory):
    """Postcode data factory."""

    id = 2656
    ccg = 'S03000012'
    ced = 'S99999999'
    eer = 'S15000001'
    imd = 3888
    lat = 57.148232
    pcd = 'AB101AA'
    pct = 'S03000012'
    pfa = 'S23000009'
    rgn = 'S99999999'
    stp = 'S99999999'
    ctry = 'S92000003'
    lep1 = 'S99999999'
    lep2 = 'S99999999'
    long = -2.096648
    nuts = 'S30000026'
    oa01 = 'S00000036'
    oa11 = 'S00090540'
    park = 'S99999999'
    pcd2 = 'AB10 1AA'
    pcds = 'AB10 1AA'
    pcon = 'S14000001'
    ttwa = 'S22000047'
    wz11 = 'S34000028'
    bua11 = 'S99999999'
    nhser = 'S99999999'
    oac01 = '2A1'
    oac11 = '2B1'
    oscty = 'S99999999'
    streg = 0
    calncv = 'S99999999'
    dointr = '2011-09-01'
    doterm = '2016-10-01'
    lsoa01 = 'S01000125'
    lsoa11 = 'S01006646'
    msoa01 = 'S02000024'
    msoa11 = 'S02001261'
    oslaua = 'S12000033'
    osward = 'S13002842'
    parish = 'S99999999'
    teclec = 'S09000001'
    buasd11 = 'S99999999'
    casward = '01C28'
    ru11ind = '1'
    ur01ind = '1'
    oseast1m = '394251'
    osgrdind = 1
    oshlthau = 'S08000020'
    osnrth1m = '0806376'
    usertype = 1
    statsward = '99ZZ00'
    region_name = 'Scotland'
    pcd_normalised = 'AB101AA'
    uk_super_region = None
    publication_date = '2022-11-01'
    local_authority_district_name = 'Aberdeen City'
    parliamentary_constituency_name = None
    lep1_local_enterprise_partnership_name = None
    lep2_local_enterprise_partnership_name = None

    class Meta:
        model = 'metadata.PostcodeData'
