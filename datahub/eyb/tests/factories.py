import factory


class EYBLeadFactory(factory.django.DjangoModelFactory):
    """EYBLead factory."""

    # EYB Triage data
    triage_id = 96
    triage_hashed_uuid = "b85dabe2a4c46828424d61ec99f496d91952f9e53733898ff5f0fee89f08b635"
    triage_created = "2023-09-21 07:53:19.534794+00"
    triage_modified = "2023-09-27 11:32:28.853014+00"
    sector = "FOOD_AND_DRINK"
    sector_sub = "PROCESSING_AND_PRESERVING_OF_MEAT"
    intent = [
        "SET_UP_NEW_PREMISES",
        "SET_UP_A_NEW_DISTRIBUTION_CENTRE",
        "ONWARD_SALES_AND_EXPORTS_FROM_THE_UK",
    ]
    intent_other = ""
    location = "NORTHERN_IRELAND"
    location_city = "ARMAGH_CITY"
    location_none = False
    hiring = "51-100"
    spend = "1000000-2000000"
    spend_other = "1234565432"
    is_high_value = True

    # EYB User data
    user_id = 90
    user_hashed_uuid = "b85dabe2a4c46828424d61ec99f496d91952f9e53733898ff5f0fee89f08b635"
    user_created = "2023-09-21 07:53:19.47271+00"
    user_modified = "2023-09-21 07:53:19.472723+00"
    company_name = "Stu co"
    company_location = "FR"
    full_name = "John Doe"
    role = "Director"
    email = "foo@bar.com"
    telephone_number = "447923454678"
    agree_terms = True
    agree_info_email = False
    landing_timeframe = "SIX_TO_TWELVE_MONTHS"
    company_website = "http://www.google.com"

    class Meta:
        model = 'eyb.EYBLead'
