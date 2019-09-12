from enum import Enum


class Template(Enum):
    """GOV.UK notifications template ids."""

    generic_order_info = '53055338-6acd-4dd6-b315-d1bd74015eb2'

    order_created_for_post_manager = '335f5402-f610-43ef-bfcf-e196215b3cf1'
    order_created_for_regional_manager = '15a7824a-b179-4ffb-a8a1-74ba89285e20'
    you_have_been_added_for_adviser = '1c631f72-4d33-41f5-ba9b-12862b5b273a'
    you_have_been_removed_for_adviser = '07668530-2dc1-4dde-9a12-9144fc303eb7'

    order_paid_for_customer = 'a6bc0d8a-a183-4345-9945-81e71aac4b3b'
    order_paid_for_adviser = 'd41e9cb2-b412-44cf-9000-a1e34d996f16'
    order_completed_for_adviser = 'a76f3841-bf70-40e7-9aa0-fd83f3dcc03c'
    order_cancelled_for_customer = '3f30d3b0-78cb-4b1b-a2bc-9c19b0aeedf4'
    order_cancelled_for_adviser = '723583be-af37-4e13-b2b0-ea496de5450e'

    quote_sent_for_customer = '5b68a6e2-539f-4b1b-8c54-0ead23c7ca1b'
    quote_sent_for_adviser = '77157de5-43b3-4988-a4e9-c6073c18be47'
    quote_accepted_for_customer = 'fbd023bd-d043-4a5b-857a-ffd1d81ca5a5'
    quote_accepted_for_adviser = 'd7b7f327-f814-4eed-9130-0a2ef988691f'
    quote_cancelled_for_customer = '86dd03cd-53b6-41b2-9eed-c3d2f6a0fda1'
    quote_cancelled_for_adviser = 'a36fff71-e62b-4d51-a374-4cdf3e50ac47'


OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME = 'omis_use_notification_app'
