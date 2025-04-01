from django.core.validators import RegexValidator


class TelephoneValidator(RegexValidator):
    """Validator for telephone numbers.

    Validates that phone number is composed of characters found in telephone numbers -
    0-9, a space or open / close brackets.
    """

    regex = r'^[\d() ]{1,}$'
    message = (
        'Phone number must be composed of numeric characters. Country code should be entered '
        'separately.'
    )


class InternationalTelephoneValidator(RegexValidator):
    """Validator for international telephone numbers.

    Validates that a phone number is composed of characters found in telephone numbers:
    0-9, spaces, hyphens, full stops, or open/close brackets, optionally preceded with a plus sign.
    Extensions can be included using 'ext' or 'x' followed by digits.
    """

    regex = r'^\+?[\d().\- ]+(?:\s*(?:ext|ext.|x)\s*\d+)?$'
    message = (
        'Phone number must be composed of valid characters. '
        'These include: 0-9, spaces, hyphens, full stops, or open/close brackets, '
        'optionally preceded with a plus sign. Extensions can be included using '
        "'ext' or 'x' followed by digits."
    )


class TelephoneCountryCodeValidator(RegexValidator):
    """Validator for telephone number country code."""

    regex = r'^\+?\d{1,4}$'
    message = 'Country code should consist of one to four numbers'
