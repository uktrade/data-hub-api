def get_address_area_or_none(address_area):
    """
    Get Formatted Address Area Result
    :param address_area: Address object returned on Company
    :return: Address as an id name object or None
    """
    return address_area and {
        'id': str(address_area.id),
        'name': address_area.name,
    } or None
