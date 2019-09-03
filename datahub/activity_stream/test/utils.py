from rest_framework.reverse import reverse


def get_url(name):
    """
    Returns the URL for test server given the endpoint name.
    """
    return 'http://testserver' + reverse(name)
