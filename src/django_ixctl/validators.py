import ipaddress
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_ip_v4(value):
    try:
        ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        raise ValidationError(_("valid ipv4 address expected"))


def validate_ip_v6(value):
    try:
        ipaddress.IPv6Address(value)
    except ipaddress.AddressValueError:
        raise ValidationError(_("valid ipv6 address expected"))
