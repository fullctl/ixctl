from django.utils.translation import ugettext_lazy as _
from django_inet.rest import IPAddressField
from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import (
    ModelSerializer,
)
import django_ixctl.models.ixctl as models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

Serializers, register = serializer_registry()


@register
class InternetExchange(ModelSerializer):

    org_id = serializers.SerializerMethodField()

    class Meta:
        model = models.InternetExchange
        fields = [
            "org_id",
            "id",
            "name",
        ]


    def get_org_id(self, ix):
        return ix.instance.org.permission_id


@register
class InternetExchangeMember(ModelSerializer):
    ix = serializers.SerializerMethodField()

    class Meta:
        model = models.InternetExchangeMember
        fields = [
            "id",
            "ix_id",
            "ix",
            "name",
            "speed",
            "asn",
            "ipaddr4",
            "ipaddr6",
            "is_rs_peer",
        ]

    def get_ix(self, member):
        if "ix" in self.context.get("joins", []):
            return InternetExchange(instance=member.ix).data
        return None
