from enum import Enum


class Template(Enum):
    """GOV.UK notifications template ids."""

    generic_order_info = 'd2a758c5-7fa0-4ac5-8ba0-653aa3ef2133'
    order_created_for_post_manager = '335f5402-f610-43ef-bfcf-e196215b3cf1'
    you_have_been_added_for_adviser = '1c631f72-4d33-41f5-ba9b-12862b5b273a'
    quote_sent_for_customer = '5b68a6e2-539f-4b1b-8c54-0ead23c7ca1b'
