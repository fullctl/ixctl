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
    class Meta:
        model = models.InternetExchange
        fields = [
            "id",
            "org_id",
            "name",
            "name_long",
            "aka",
            "city",
            "country",
            "region_continent",
            "tech_email",
            "tech_phone",
            "policy_email",
            "policy_phone",
            "service_level",
            "terms",
            "media",
            "url_stats",
            "website",
        ]


@register
class InternetExchangeMember(ModelSerializer):
    net = serializers.SerializerMethodField()
    ix_id = serializers.IntegerField(source="ixlan_id")
    ix = serializers.SerializerMethodField()

    class Meta:
        model = models.InternetExchangeMember
        fields = [
            "id",
            "net",
            "net_id",
            "ixlan_id",
            "ix_id",
            "ix",
            "speed",
            "asn",
            "ipaddr4",
            "ipaddr6",
            "is_rs_peer",
            "operational",
        ]

    def get_net(self, netixlan):
        if "net" in self.context.get("joins", []):
            return Network(instance=netixlan.net).data
        return None

    def get_ix(self, netixlan):
        if "ix" in self.context.get("joins", []):
            return InternetExchange(instance=netixlan.ixlan.ix).data
        return None

