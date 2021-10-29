from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer
from rest_framework import serializers

import django_ixctl.models.ixctl as models

Serializers, register = serializer_registry()


@register
class InternetExchange(ModelSerializer):

    org_id = serializers.SerializerMethodField()

    class Meta:
        model = models.InternetExchange
        fields = [
            "org_id",
            "id",
            "pdb_id",
            "name",
        ]

    def get_org_id(self, ix):
        return ix.instance.org.permission_id


@register
class InternetExchangeMember(ModelSerializer):
    ix = serializers.SerializerMethodField()
    pdb_ix_id = serializers.SerializerMethodField()

    class Meta:
        model = models.InternetExchangeMember
        fields = [
            "id",
            "ix_id",
            "pdb_ix_id",
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

    def get_pdb_ix_id(self, member):
        return member.ix.pdb_id
