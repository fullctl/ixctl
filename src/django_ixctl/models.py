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

from django_grainy.decorators import grainy_model

from django_inet.models import (
    IPAddressField,
    MacAddressField,
    ASNField,
)


import reversion

from django_handleref.models import HandleRefModel as SoftDeleteHandleRefModel
from django_peeringdb.models.concrete import IXLan, NetworkIXLan

from django_ixctl.inet.util import pdb_lookup
from django_ixctl.validators import validate_ip_v4, validate_ip_v6
from django_ixctl.peeringdb import get_as_set

import django_ixctl.enum


def generate_secret():
    return token_urlsafe()


class HandleRefModel(SoftDeleteHandleRefModel):
    """
    Like handle ref, but with hard delete
    and extended status types
    """

    status = models.CharField(
        max_length=12,
        default="ok",
        choices=(
            ("ok", _("Ok")),
            ("pending", _("Pending")),
            ("deactivated", _("Deactivated")),
            ("failed", _("Failed")),
            ("expired", _("Expired")),
        ),
    )

    class Meta:
        abstract = True

    def delete(self):
        return super().delete(hard=True)


class PdbRefModel(HandleRefModel):

    """
    Base class for models that reference a peeringdb model
    """

    # id of the peeringdb instance that is referenced by
    # this model
    pdb_id = models.PositiveIntegerField(blank=True, null=True)

    # if object was creates from it's pdb reference, the version
    # at the time of the creation should be stored here
    pdb_version = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        abstract = True

    class PdbRef:
        """ defines which peeringdb model is referenced """

        model = NetworkIXLan
        fields = {"pk": "pdb_id"}

    @classmethod
    def create_from_pdb(cls, pdb_object, save=True, **fields):
        """ create object from peeringdb instance """

        if not isinstance(pdb_object, cls.PdbRef.model):
            raise ValueError(_(f"Expected {cls.PdbRef.model} instance"))

        for k, v in cls.PdbRef.fields.items():
            fields[v] = getattr(pdb_object, k, k)

        instance = cls(status="ok", **fields)
        if save:
            instance.save()
        return instance

    @property
    def pdb(self):
        """ returns PeeringDB object """
        if not hasattr(self, "_pdb"):
            filters = {}
            for k, v in self.PdbRef.fields.items():
                if v and hasattr(self, v):
                    v = getattr(self, v)
                filters[k] = v
            self._pdb = pdb_lookup(self.PdbRef.model, **filters)
        return self._pdb


@reversion.register()
@grainy_model(
    namespace="account.org", namespace_instance="account.org.{instance.permission_id}"
)
class Organization(HandleRefModel):

    """
    Describes an organization
    """

    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=64, unique=True)
    personal = models.BooleanField(default=False)

    # if oauth manages organizations these will describe a reference
    # to the backend that created the organization

    backend = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Authentication service that created this org"),
    )
    remote_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text=_(
            "If the authentication service is in control of the organizations this field will hold a reference to the id at the auth service"
        ),
    )

    permission_namespaces = [
        "management",
        "ixctl",
    ]

    class HandleRef:
        tag = "org"


    @property
    def permission_id(self):
        if self.remote_id:
            return self.remote_id
        return self.id

    @classmethod
    def sync(cls, orgs, user, backend):
        synced = []
        with reversion.create_revision():
            reversion.set_user(user)
            for org_data in orgs:
                org = cls.sync_single(org_data, user, backend)
                synced.append(org)

            for org in user.org_set.exclude(org__remote_id__in=[o["id"] for o in orgs]):
                org.delete()
        return synced

    @classmethod
    def sync_single(cls, data, user, backend):
        try:
            changed = False
            org = cls.objects.get(remote_id=data["id"], backend=backend)
            if data["slug"] != org.slug:
                org.slug = data["slug"]
                changed = True
            if data["name"] != org.name:
                org.name = data["name"]
                changed = True
            if data["personal"] != org.personal:
                org.personal = data["personal"]
                changed = True
            if changed:
                org.save()
        except cls.DoesNotExist:
            org = cls.objects.create(
                remote_id=data["id"],
                backend=backend,
                name=data["name"],
                slug=data["slug"],
                personal=data["personal"],
            )

        if not user.org_set.filter(org=org).exists():
            OrganizationUser.objects.create(org=org, user=user)

        return org

    @property
    def tag(self):
        return self.slug

    @property
    def display_name(self):
        if self.personal:
            return _("Personal")
        return self.name

    def __str__(self):
        return f"{self.name} ({self.slug})"


@grainy_model(namespace="org")
class Instance(HandleRefModel):

    """
    app instance, one per org per app

    Needs to specify an `org` ForeignKey pointing to
    Organization
    """

    org = models.ForeignKey(
        Organization, help_text=_("owned by org"), on_delete=models.CASCADE
    )
    secret = models.CharField(max_length=255, default=generate_secret)
    app_id = "ixctl"

    class Meta:
        db_table = "ixctl_instance"

    class HandleRef:
        tag = "instance"

    @classmethod
    def get_or_create(cls, org):
        """
        Returns an organization's instance

        Will create a new instance if it does not exist
        """

        try:
            instance = cls.objects.get(org=org)
        except cls.DoesNotExist:
            instance = cls.objects.create(org=org, status="ok")
        return instance

    def __str__(self):
        return f"{self.org} ({self.id})"


@reversion.register()
@grainy_model(namespace="org")
class OrganizationUser(HandleRefModel):

    """
    Describes a user -> organization relationship
    """

    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="user_set"
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="org_set"
    )

    class HandleRef:
        tag = "orguser"

    class Meta:
        db_table = "ixctl_org_user"
        verbose_name = _("Organization User")
        verbose_name = _("Organization Users")

    def __str__(self):
        return f"{self.user.username} <{self.user.email}>"


@reversion.register
@grainy_model(namespace="org")
class APIKey(HandleRefModel):
    """
    Describes an APIKey

    These are managed in account.20c.com, but will also be cached here

    Creation should always happen at account.20c.com
    """

    key = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="key_set"
    )

    class Meta:
        db_table = "ixctl_api_key"
        verbose_name = _("API Key")
        verbose_name_plural = _("API Keys")

    class HandleRef:
        tag = "key"


@reversion.register()
@grainy_model(namespace="ix")
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
            "django_ixctl:ixf export", args=(ix.instance.org.slug, ix.secret,)
        )

    def __str__(self):
        return f"{self.name} ({self.id})"


@reversion.register()
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
        max_length=255, blank=True, null=True, validators=[validate_ip_v4]
    )
    ipaddr6 = models.CharField(
        max_length=255, blank=True, null=True, validators=[validate_ip_v6]
    )
    macaddr = MacAddressField(null=True, blank=True)
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


@reversion.register
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
                clients[member.asn] = {"asn": member.asn, "ip": []}

            if member.ipaddr4:
                clients[member.asn]["ip"].append(f"{member.ipaddr4}")

            if member.ipaddr6:
                clients[member.asn]["ip"].append(f"{member.ipaddr6}")

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
