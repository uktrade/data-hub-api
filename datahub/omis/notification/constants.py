from enum import Enum


class Template(Enum):
    """GOV.UK notifications template ids."""

    generic_order_info = 'd2a758c5-7fa0-4ac5-8ba0-653aa3ef2133'
    order_created_for_post_manager = '335f5402-f610-43ef-bfcf-e196215b3cf1'
    you_have_been_added_for_adviser = '1c631f72-4d33-41f5-ba9b-12862b5b273a'
    quote_sent_for_customer = '5b68a6e2-539f-4b1b-8c54-0ead23c7ca1b'
    quote_sent_for_adviser = '77157de5-43b3-4988-a4e9-c6073c18be47'
    order_cancelled_for_customer = '3f30d3b0-78cb-4b1b-a2bc-9c19b0aeedf4'
    order_cancelled_for_adviser = '723583be-af37-4e13-b2b0-ea496de5450e'
    quote_accepted_for_customer = 'fbd023bd-d043-4a5b-857a-ffd1d81ca5a5'
    quote_accepted_for_adviser = 'd7b7f327-f814-4eed-9130-0a2ef988691f'
    order_completed_for_adviser = 'a76f3841-bf70-40e7-9aa0-fd83f3dcc03c'
