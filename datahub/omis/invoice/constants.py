from datahub.core import constants

DIT_COMPANY_NAME = 'Department for Business and Trade'
DIT_ADDRESS_1 = 'Old Admiralty Building'
DIT_ADDRESS_2 = 'Admiralty Place'
DIT_ADDRESS_TOWN = 'London'
DIT_ADDRESS_COUNTY = ''
DIT_ADDRESS_POSTCODE = 'SW1A 2DY'
DIT_ADDRESS_COUNTRY_ID = constants.Country.united_kingdom.value.id
DIT_VAT_NUMBER = '888 850455'


# used to calculate the payment due date, that is whichever is earliest of
# [delivery date - PAYMENT_DUE_DAYS_BEFORE_DELIVERY days] OR
# [date quote accepted + PAYMENT_DUE_DAYS_FROM_NOW days]
PAYMENT_DUE_DAYS_BEFORE_DELIVERY = 14
PAYMENT_DUE_DAYS_FROM_NOW = 30
