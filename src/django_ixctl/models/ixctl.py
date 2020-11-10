import time
import os.path
import tempfile
import subprocess

from secrets import token_urlsafe

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import yaml

from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings

from django_grainy.decorators import grainy_model

from django_inet.models import (
    IPAddressField,
    MacAddressField,
    ASNField,
)


import reversion


from django_peeringdb.models.concrete import IXLan, NetworkIXLan, Network
from fullctl.django.models.concrete import (
    Organization,
    OrganizationUser,
    Instance,
    APIKey,
)
from fullctl.django.models.abstract.base import HandleRefModel, PdbRefModel

from fullctl.django.auth import permissions
from fullctl.django.inet.util import pdb_lookup
from fullctl.django.inet.validators import validate_ip4, validate_ip6, validate_as_set


from django_ixctl.peeringdb import get_as_set
import django_ixctl.enum


def generate_secret():
    return token_urlsafe()


@reversion.register
@grainy_model(namespace="org")
class PermissionRequest(HandleRefModel):
    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="permreq_set"
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="permreq_set"
    )
    type = models.CharField(
        max_length=255,
        choices=django_ixctl.enum.PERMISSION_REQUEST_TYPES,
    )
    extra = models.TextField(null=True, blank=True)

    class HandleRef:
        tag = "permreq"

    class Meta:
        db_table = "ixctl_permreq"
        verbose_name = _("Permission Request")
        verbose_name_plural = _("Permission Requests")

    def __str__(self):
        return f"Permission Request: {self.user} -> {self.org}"


@reversion.register()
@grainy_model(namespace="ix", namespace_instance="ix.{instance.org.permission_id}.{instance.id}")
class InternetExchange(PdbRefModel):

    """
    Describes an internet exchange

    Can have a reference to a peeringdb ixlan object
    """

    name = models.CharField(max_length=255, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    urlkey = models.CharField(max_length=255, default=generate_secret, unique=True)

    instance = models.ForeignKey(
        Instance, related_name="ix_set", on_delete=models.CASCADE, null=True
    )

    class PdbRef(PdbRefModel.PdbRef):
        model = IXLan

    class HandleRef:
        tag = "ix"

    class Meta:
        db_table = "ixctl_ix"
        verbose_name_plural = _("Internet Exchanges")
        verbose_name = _("Internet Exchange")

    @classmethod
    def create_from_pdb(cls, instance, pdb_object, save=True, **fields):

        """
        create instance from peeringdb ixlan

        Argument(s):

        - instance (`Instance`): instance that contains this exchange
        - pdb_object (`django_peeringdb.IXLan`): pdb ixlan instance
        - save (`bool`): if True commit to the database, otherwise dont

        Keyword Argument(s):

        Any arguments passed will be used to set properties on the
        object before creation

        Returns:

        - `InternetExchange` instance
        """

        ix = super().create_from_pdb(pdb_object, save=save, instance=instance, **fields)

        ix.name = pdb_object.ix.name

        if save:
            ix.save()

        for netixlan in ix.pdb.netixlan_set.filter(status="ok"):
            InternetExchangeMember.create_from_pdb(netixlan, ix=ix)

        return ix

    @property
    def display_name(self):
        """
        Will return the exchange name if specified.

        If self.name is not specified and pdb reference is set return
        the name of the peeringdb ix instead

        If peeringdb reference is not specified either, return
        generic "Nameless Exchange ({id})"
        """

        if self.name:
            return self.name
        if self.pdb_id:
            return self.pdb.ix.name
        return f"Nameless Exchange ({self.id})"

    @property
    def ixf_export_url(self):
        """
        Returns the path for the ix-f export URL for this
        exchange
        """

        return reverse(
            "ixf export", args=(self.instance.org.slug, self.instance.secret,)
        )

    @property
    def org(self):
        return self.instance.org


    def __str__(self):
        return f"{self.name} ({self.id})"


@reversion.register()
@grainy_model(
    namespace="member",
    namespace_instance="member.{instance.org.permission_id}.{instance.ix_id}.{instance.asn}"
)
class InternetExchangeMember(PdbRefModel):

    """
    Describes a member at an internet exchange

    Can have a reference to a peeringdb netixlan object
    """

    ix = models.ForeignKey(
        InternetExchange,
        help_text=_("Members at this Exchange"),
        related_name="member_set",
        on_delete=models.CASCADE,
    )
    ipaddr4 = models.CharField(
        max_length=255, blank=True, null=True, validators=[validate_ip4]
    )
    ipaddr6 = models.CharField(
        max_length=255, blank=True, null=True, validators=[validate_ip6]
    )
    macaddr = MacAddressField(null=True, blank=True)
    as_macro = models.CharField(
        max_length=255, blank=True, null=True, validators=[validate_as_set]
    )
    is_rs_peer = models.BooleanField(default=False)
    speed = models.PositiveIntegerField()
    asn = models.PositiveIntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)

    ixf_state = models.CharField(max_length=255, default="active")
    ixf_member_type = models.CharField(
        max_length=255, choices=django_ixctl.enum.IXF_MEMBER_TYPE, default="peering"
    )

    class HandleRef:
        tag = "member"

    class Meta:
        db_table = "ixctl_member"
        verbose_name_plural = _("Internet Exchange Members")
        verbose_name = _("Internet Exchange Member")
        unique_together = (("ipaddr4", "ix"), ("ipaddr6", "ix"), ("macaddr", "ix"))

    @classmethod
    def create_from_pdb(cls, pdb_object, ix, save=True, **fields):

        """
        Create `InternetExchangeMember` from peeringdb netixlan

        Argument(s):

        - pdb_object (`django_peeringdb.NetworkIXLan`): netixlan instance
        - ix (`InternetExchange`): member of this ix

        Keyword Argument(s):

        And keyword arguments passwed will be used to inform properties
        of the InternetExchangeMember to be created
        """

        member = super().create_from_pdb(pdb_object, ix=ix, save=False, **fields)

        member.ipaddr4 = pdb_object.ipaddr4
        member.ipaddr6 = pdb_object.ipaddr6
        member.is_rs_peer = pdb_object.is_rs_peer
        member.speed = pdb_object.speed
        member.asn = pdb_object.net.asn
        member.name = pdb_object.net.name

        if save:
            member.save()

        return member

    @property
    def display_name(self):
        return self.name or f"AS{self.asn}"

    @property
    def org(self):
        return self.ix.instance.org

    @property
    def ix_name(self):
        return self.ix.name

    @property
    def as_sets(self):
        if not self.as_macro:
            return []

        return [as_set.strip() for as_set in self.as_macro.split(",")]


@reversion.register
@grainy_model(
    namespace="rs",
    namespace_instance="rs.{instance.org.permission_id}.{instance.ix_id}.{instance.asn}"
)
class Routeserver(HandleRefModel):

    """
    Describes a routeserver at an internet exchange
    """

    ix = models.ForeignKey(
        InternetExchange, on_delete=models.CASCADE, related_name="rs_set",
    )

    # RS Config

    name = models.CharField(max_length=255, help_text=_("Routeserver name"),)

    asn = ASNField(help_text=_("ASN"))

    router_id = IPAddressField(version=4, help_text=_("Router Id"),)

    rpki_bgp_origin_validation = models.BooleanField(default=False)

    # ARS Config

    ars_type = models.CharField(
        max_length=32, choices=django_ixctl.enum.ARS_TYPES, default="bird",
    )

    max_as_path_length = models.IntegerField(
        default=32, help_text=_("Max length of AS_PATH attribute."),
    )

    no_export_action = models.CharField(
        max_length=8,
        choices=django_ixctl.enum.ARS_NO_EXPORT_ACTIONS,
        default="pass",
        help_text=_("RFC1997 well-known communities (NO_EXPORT and NO_ADVERTISE)"),
    )

    graceful_shutdown = models.BooleanField(
        default=False, help_text=_("Graceful BGP session shutdown"),
    )

    extra_config = models.TextField(
        null=True, blank=True, help_text=_("Extra arouteserver config")
    )

    class Meta:
        db_table = "ixctl_rs"
        unique_together = (("ix", "router_id"),)

    class HandleRef:
        tag = "rs"

    @property
    def org(self):
        return self.ix.instance.org

    @property
    def display_name(self):
        return self.name

    @property
    def rsconf(self):
        """
        Return the rsconf instance for this routeserver

        Will create the rsconf instance if it does not exist yet
        """
        if not hasattr(self, "_rsconf"):
            rsconf, created = RouteserverConfig.objects.get_or_create(rs=self)
            self._rsconf = rsconf
        return self._rsconf

    @property
    def ars_general(self):

        """
        Generate and return `dict` for ARouteserver general config
        """

        ars_general = {
            "cfg": {
                "rs_as": self.asn,
                "router_id": f"{self.router_id}",
                "filtering": {
                    "max_as_path_len": self.max_as_path_length,
                    "rpki_bgp_origin_validation": {
                        "enabled": self.rpki_bgp_origin_validation
                    },
                },
                "rfc1997_wellknown_communities": {"policy": self.no_export_action,},
                "graceful_shutdown": {"enabled": self.graceful_shutdown},
            }
        }

        if self.extra_config:
            extra_config = yaml.load(self.extra_config, Loader=Loader)

            # TODO: should we expect people to put the cfg:
            # root element into the extra config or not ?
            #
            # support both approaches for now

            if "cfg" in extra_config:
                ars_general["cfg"].update(extra_config["cfg"])
            else:
                ars_general.update(extra_config)

        return ars_general

    @property
    def ars_clients(self):

        """
        Generate and return `dirct` for ARouteserver clients config
        """

        asns = {}
        clients = {}

        # TODO
        # where to get ASN sets from ??
        # peeringdb network ??

        for member in self.ix.member_set.filter(is_rs_peer=True):
            asn = f"AS{member.asn}"
            if asn not in asns:
                if member.pdb_id:
                    as_set = get_as_set(member.pdb.net)
                    if as_set:
                        asns[asn] = {"as_sets": [as_set]}

            if member.asn not in clients:
                clients[member.asn] = {"asn": member.asn, "ip": [], "cfg": {}}

            if member.ipaddr4:
                clients[member.asn]["ip"].append(f"{member.ipaddr4}")

            if member.ipaddr6:
                clients[member.asn]["ip"].append(f"{member.ipaddr6}")

            if member.as_macro:
                clients[member.asn]["cfg"].update(
                    filtering={
                        "irrdb": {
                            "as_sets": member.as_sets,
                        }
                    }
                )

        return {"asns": asns, "clients": list(clients.values())}

    def __str__(self):
        return f"Routeserver {self.name} AS{self.asn}"


@reversion.register
class RouteserverConfig(HandleRefModel):

    """
    Describes a configuration (aroutserver generated) for a
    `Routeserver` instance
    """

    rs = models.OneToOneField(
        Routeserver, on_delete=models.CASCADE, null=True, blank=True,
    )

    generated = models.DateTimeField(
        auto_now=True, blank=True, help_text=_("Time of generation")
    )

    # TODO: rename to `config` ?
    # Once we have confu backed config fields
    # i sort of want the `config` attribute to be
    # reserved for confu config fields though.

    body = models.TextField(help_text=_("Config content"))

    ars_general = models.TextField(
        help_text=("ARouteserver general config"), null=True, blank=True
    )
    ars_clients = models.TextField(
        help_text=("ARouteserver clients config"), null=True, blank=True
    )

    class HandleRef:
        tag = "rsconf"

    class Meta:
        db_table = "ixctl_rsconf"

    @property
    def outdated(self):

        """
        Returns whether or not the config needs to be regenerated
        """

        # Route server has been updated since last generation,

        if not self.generated or self.generated < self.rs.updated:
            return True

        # RS Peer has been updated since last generation

        for member in self.rs.ix.member_set.filter(is_rs_peer=True):
            if self.generated < member.updated:
                return True
        return False

    def generate(self):

        """
        Generate the route server config using arouteserver
        """

        ix = self.rs.ix
        rs = self.rs
        ars_general = rs.ars_general
        ars_clients = rs.ars_clients

        config_dir = tempfile.mkdtemp(prefix="ixctl_rsconf")

        general_config_file = os.path.join(config_dir, "general.yaml")
        clients_config_file = os.path.join(config_dir, "clients.yaml")
        outfile = os.path.join(config_dir, "generated-config.txt")

        with open(general_config_file, "w") as fh:
            as_yaml = yaml.dump(ars_general, Dumper=Dumper)
            self.ars_general = as_yaml
            fh.write(as_yaml)

        with open(clients_config_file, "w") as fh:
            as_yaml = yaml.dump(ars_clients, Dumper=Dumper)
            self.ars_clients = as_yaml
            fh.write(as_yaml)

        # no reasonable way found to call an arouteserve
        # python api - so lets just run the command

        if rs.ars_type in ["bird", "bird2"]:
            ars_type = "bird"
        else:
            ars_type = rs.ars_type

        cmd = [
            "arouteserver",
            ars_type,
            "--general",
            general_config_file,
            "--clients",
            clients_config_file,
            "-o",
            outfile,
        ]

        # TODO: bird v1 needs to generate
        # separate for each ip version
        #
        # how to store?

        if rs.ars_type == "bird":
            cmd += ["--ip-ver", "4"]
        elif rs.ars_type == "bird2":
            cmd += ["--target-version", "2.0.7"]

        process = subprocess.Popen(cmd)
        process.wait(600)

        with open(outfile) as fh:
            self.body = fh.read()

        self.save()

@reversion.register()
@grainy_model(namespace="net", namespace_instance="net.{instance.org.permission_id}.{instance.asn}")
class Network(PdbRefModel):

    """
    Describes a network

    Can have a reference to a peeringdb netlan object
    """

    name = models.CharField(max_length=255, blank=False)
    asn = models.IntegerField()
    instance = models.ForeignKey(
        Instance, related_name="net_set", on_delete=models.CASCADE, null=True
    )

    class PdbRef(PdbRefModel.PdbRef):
        model = Network
        fields = {"asn": "pdb_id"}

    class HandleRef:
        tag = "net"

    class Meta:
        db_table = "ixctl_net"
        verbose_name_plural = _("Networks")
        verbose_name = _("Network")
        unique_together = (
            ("instance", "asn"),
        )

    @classmethod
    def create_from_pdb(cls, instance, pdb_object, save=True, **fields):

        """
        create instance from peeringdb network

        Argument(s):

        - instance (`Instance`): instance that contains this network
        - pdb_object (`django_peeringdb.Network`): pdb network
        - save (`bool`): if True commit to the database, otherwise dont

        Keyword Argument(s):

        Any arguments passed will be used to set properties on the
        object before creation

        Returns:

        - `Network` instance
        """

        net = super().create_from_pdb(pdb_object, save=save, instance=instance, name=pdb_object.name, asn=pdb_object.asn, **fields)

        return net

    @property
    def display_name(self):
        """
        Will return the exchange name if specified.

        If self.name is not specified and pdb reference is set return
        the name of the peeringdb ix instead

        If peeringdb reference is not specified either, return
        generic "Nameless Exchange ({id})"
        """

        if self.name:
            return self.name
        if self.pdb_id:
            return self.pdb.name
        return f"Unknown Network (AS{self.asn})"

    @property
    def org(self):
        return self.instance.org

    @property
    def members(self):
        if not hasattr(self, "_members"):
            self._members = [
                member for member in
                InternetExchangeMember.objects.filter(
                    asn = self.asn
                )
            ]
        return self._members

    def __str__(self):
        return f"{self.name} (AS{self.asn})"
