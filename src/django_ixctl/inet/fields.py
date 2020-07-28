from django.db import models
from django_inet.models import (
    IPAddressField as IPAddressFieldOld,
    IPPrefixField as IPPrefixFieldOld,
)


class IPPrefixField(IPPrefixFieldOld):
    def value_to_string(self, obj):
        return str(self.value_from_object(obj))


class IPAddressField(IPAddressFieldOld):
    def value_to_string(self, obj):
        return str(self.value_from_object(obj))


class DeviceDescriptionField(models.CharField):
    """
    description field for use with devices
    will need template replacement and valid char checking
    """

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 255
        kwargs["blank"] = True
        kwargs["null"] = True
        super().__init__(*args, **kwargs)
