"""Phone number normalization to E.164 format using phonenumbers library."""

import phonenumbers


# Default country codes for parsing numbers without international prefix
COUNTRY_DEFAULTS = {
    "ES": "ES",
    "GB": "GB",
    "US": "US",
    "MX": "MX",
    "CO": "CO",
    "CL": "CL",
    "CA": "CA",
    "AR": "AR",
}


def normalize_phone_e164(phone: str, country_code: str = "ES") -> str | None:
    """Normalize a phone number to E.164 format.

    Args:
        phone: Raw phone number string (any format)
        country_code: ISO 3166-1 alpha-2 country code for parsing

    Returns:
        E.164 formatted number (e.g. "+34612345678") or None if invalid
    """
    if not phone or not phone.strip():
        return None

    region = COUNTRY_DEFAULTS.get(country_code, country_code)

    try:
        parsed = phonenumbers.parse(phone, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass

    return None


def is_mobile(phone_e164: str) -> bool | None:
    """Check if an E.164 number is a mobile phone.

    Returns True for mobile, False for fixed, None if unknown.
    """
    if not phone_e164:
        return None

    try:
        parsed = phonenumbers.parse(phone_e164)
        number_type = phonenumbers.number_type(parsed)
        if number_type == phonenumbers.PhoneNumberType.MOBILE:
            return True
        elif number_type == phonenumbers.PhoneNumberType.FIXED_LINE:
            return False
        return None
    except phonenumbers.NumberParseException:
        return None


def format_national(phone_e164: str) -> str:
    """Format E.164 number in national format for display."""
    if not phone_e164:
        return ""

    try:
        parsed = phonenumbers.parse(phone_e164)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
    except phonenumbers.NumberParseException:
        return phone_e164
