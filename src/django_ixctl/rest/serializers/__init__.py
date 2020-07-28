from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class RequireContext(object):

    required_context = []

    def validate(self, data):
        data = super().validate(data)

        for key in self.required_context:
            if key not in self.context:
                raise serializers.ValidationError(_("Context missing: {}".format(key)))

        return data
