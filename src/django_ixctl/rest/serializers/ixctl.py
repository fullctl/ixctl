try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import yaml

from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

import django_ixctl.models as models

import django_peeringdb.models.concrete as pdb_models

from django_ixctl.rest.decorators import serializer_registry
from django_ixctl.rest.serializers import RequireContext
from django_inet.rest import IPAddressField

from django_ixctl.peeringdb import (
    import_exchange,
    import_org,
)

Serializers, register = serializer_registry()


class SoftRequiredValidator(object):
    """
    A validator that allows us to require that at least
    one of the specified fields is set
    """

    message = _("This field is required")
    requires_context = True

    def __init__(self, fields, message=None):
        self.fields = fields
        self.message = message or self.message

    def set_context(self, serializer):
        self.instance = getattr(serializer, "instance", None)

    def __call__(self, attrs, serializer):
        missing = {
            field_name: self.message
            for field_name in self.fields
            if not attrs.get(field_name)
        }
        valid = len(self.fields) != len(missing.keys())
        if not valid:
            raise ValidationError(missing)


@register
class ImportOrganization(RequireContext, serializers.Serializer):

    pdb_org_id = serializers.IntegerField(required=False)

    required_context = ["instance"]

    ref_tag = "imporg"

    class Meta:
        fields = [
            "pdb_org_id",
        ]

    def validate_pdb_org_id(self, value):
        if not value:
            return 0
        try:
            self.pdb_org = pdb_models.Organization.objects.get(id=value)
        except pdb_models.Organization.DoesNotExist:
            raise ValidationError(_("Unknown peeringdb organization"))
        return self.pdb_org.id

    def save(self):
        instance = self.context.get("instance")
        pdb_org = getattr(self, "pdb_org", None)
        return import_org(pdb_org, instance)


@register
class ImportExchange(RequireContext, serializers.Serializer):

    pdb_ix_id = serializers.IntegerField()

    required_context = ["instance"]

    ref_tag = "impix"

    class Meta:
        fields = [
            "pdb_ix_id",
        ]

    def validate_pdb_ix_id(self, value):
        instance = self.context.get("instance")
        if not value:
            return 0
        try:
            self.pdb_ix = pdb_models.InternetExchange.objects.get(id=value)
        except pdb_models.InternetExchange.DoesNotExist:
            raise ValidationError(_("Unknown peeringdb organization"))

        qset = models.InternetExchange.objects.filter(
            instance=instance, pdb_id=self.pdb_ix.id
        )

        if qset.exists():
            raise ValidationError(_("You have already imported this exchange"))

        return self.pdb_ix.id

    def save(self):
        instance = self.context.get("instance")
        ix = import_exchange(self.pdb_ix, instance)
        return ix


@register
class InternetExchange(serializers.ModelSerializer):
    class Meta:
        model = models.InternetExchange
        fields = ["pdb_id", "urlkey", "name"]


@register
class InternetExchangeMember(serializers.ModelSerializer):

    ipaddr4 = IPAddressField(
        version=4, allow_blank=True, allow_null=True, required=False, default=None
    )
    ipaddr6 = IPAddressField(
        version=6, allow_blank=True, allow_null=True, required=False, default=None
    )
    macaddr = serializers.CharField(allow_blank=True, allow_null=True, required=False, default=None, validators=[RegexValidator(r'(?i)^([0-9a-f]{2}[-:]){5}[0-9a-f]{2}$')])

    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = models.InternetExchangeMember
        fields = [
            "id",
            "pdb_id",
            "ix",
            "ixf_member_type",
            "ixf_state",
            "asn",
            "name",
            "display_name",
            "ipaddr4",
            "ipaddr6",
            "macaddr",
            "is_rs_peer",
            "speed",
        ]
        validators = [
            SoftRequiredValidator(
                fields=("ipaddr4", "ipaddr6"),
                message=_("Input required for IPv4 or IPv6"),
            ),
            UniqueTogetherValidator(
                queryset=models.InternetExchangeMember.objects.all(),
                fields=("ipaddr4", "ix"),
                message="IPv4 address exists already in this exchange",
            ),
            UniqueTogetherValidator(
                queryset=models.InternetExchangeMember.objects.all(),
                fields=("ipaddr6", "ix"),
                message="IPv6 address exists already in this exchange",
            ),
        ]

    def validate_ipaddr4(self, ipaddr4):
        if not ipaddr4:
            return None
        return ipaddr4

    def validate_ipaddr6(self, ipaddr6):
        if not ipaddr6:
            return None
        return ipaddr6

    def validate_macaddr(self, macaddr):
        if not macaddr:
            return None
        return macaddr


@register
class Routeserver(serializers.ModelSerializer):

    router_id = IPAddressField(version=4,)

    class Meta:
        model = models.Routeserver
        fields = [
            "id",
            "ix",
            "name",
            "display_name",
            "asn",
            "router_id",
            "ars_type",
            "max_as_path_length",
            "no_export_action",
            "rpki_bgp_origin_validation",
            "graceful_shutdown",
            "extra_config",
        ]

    def validate_extra_config(self, value):
        try:
            data = yaml.load(value, Loader=Loader)
        except Exception as exc:
            raise serializers.ValidationError(f"Invalid yaml formatting: {exc}")

        if data and not isinstance(data, dict):
            raise serializers.ValidationError("Config object literal expected")
        return value


@register
class Routeserver(serializers.ModelSerializer):
    class Meta:
        model = models.RouteserverConfig
        fields = [
            "rs",
            "body",
        ]

@register
class OrganizationUser(serializers.ModelSerializer):
    ref_tag = "orguser"

    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    you = serializers.SerializerMethodField()

    class Meta:
        model = models.OrganizationUser
        fields = ["id", "name", "email", "you"]

    def get_name(self, obj):
        return "{} {}".format(obj.user.first_name, obj.user.last_name)

    def get_email(self, obj):
        return obj.user.email

    def get_you(self, obj):
        return obj.user == self.context.get("user")
