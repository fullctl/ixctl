import os.path
import re
import subprocess
import tempfile
from datetime import datetime
from secrets import token_urlsafe

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader, Dumper

import fullctl.service_bridge.pdbctl as pdbctl
import fullctl.service_bridge.sot as sot
import reversion
import structlog
import yaml
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_grainy.decorators import grainy_model
from django_inet.models import ASNField
from fullctl.django.inet.validators import validate_as_set
from fullctl.django.models.abstract.base import HandleRefModel, PdbRefModel
from fullctl.django.models.concrete import Instance, Organization
from netfields import InetAddressField, MACAddressField

import django_ixctl.enum
import django_ixctl.models.tasks

logger = structlog.get_logger(__name__)


def generate_secret():
    return token_urlsafe()


def get_as_set(as_set_string):
    return [as_set.strip() for as_set in re.split(r"[, ]+", as_set_string)]


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
@grainy_model(
    namespace="ix", namespace_instance="ix.{instance.org.permission_id}.{instance.id}"
)
class InternetExchange(PdbRefModel):

    """
    Describes an internet exchange

    Can have a reference to a peeringdb ixlan object
    """

    name = models.CharField(max_length=255, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    urlkey = models.CharField(max_length=255, default=generate_secret, unique=True)
    ixf_export_privacy = models.CharField(
        max_length=32,
        choices=django_ixctl.enum.IXF_EXPORT_PRIVACY_TYPES,
        default="public",
    )

    slug = models.SlugField(max_length=64, unique=False, blank=False, null=False)

    instance = models.ForeignKey(
        Instance, related_name="ix_set", on_delete=models.CASCADE, null=True
    )

    source_of_truth = models.BooleanField(
        default=False,
        help_text=_(
            "Allows other fullctl services to see ixctl as the source of truth for this exchange"
        ),
    )

    class PdbRef(PdbRefModel.PdbRef):
        pdbctl = pdbctl.InternetExchange

    class HandleRef:
        tag = "ix"

    class Meta:
        db_table = "ixctl_ix"
        verbose_name_plural = _("Internet Exchanges")
        verbose_name = _("Internet Exchange")
        constraints = [
            models.UniqueConstraint(
                fields=["instance", "slug"], name="unique_slug_instance_pair"
            )
        ]

    @classmethod
    def create_from_pdb(cls, instance, pdb_object, save=True, **fields):

        """
        create instance from peeringdb ixlan

        Argument(s):

        - instance (`Instance`): instance that contains this exchange
        - pdb_object (`fullctl.service_bridge.pdbctl.IXLan`): pdb ixlan instance
        - save (`bool`): if True commit to the database, otherwise dont

        Keyword Argument(s):

        Any arguments passed will be used to set properties on the
        object before creation

        Returns:

        - `InternetExchange` instance
        """

        ix = super().create_from_pdb(pdb_object, save=save, instance=instance, **fields)

        ix.name = pdb_object.name
        ix.slug = cls.default_slug(ix.name)

        if save:
            ix.save()

        for netixlan in pdbctl.NetworkIXLan().objects(ix=pdb_object.id, join="net"):
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
            "ixf export",
            args=(
                self.instance.org.slug,
                self.slug,
            ),
        )

    @property
    def org(self):
        return self.instance.org

    @classmethod
    def default_slug(cls, name):
        return name.replace("/", "_").replace(" ", "_").replace("-", "_").lower()

    def __str__(self):
        return f"{self.name} ({self.id})"


@reversion.register()
@grainy_model(
    namespace="member",
    namespace_instance=(
        "member.{instance.org.permission_id}.{instance.ix_id}.{instance.asn}"
    ),
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
    ipaddr4 = InetAddressField(blank=True, null=True, store_prefix_length=False)
    ipaddr6 = InetAddressField(blank=True, null=True, store_prefix_length=False)
    macaddr = MACAddressField(null=True, blank=True)
    as_macro_override = models.CharField(
        max_length=255, blank=True, null=True, validators=[validate_as_set]
    )
    md5 = models.CharField(max_length=255, null=True, blank=True)
    is_rs_peer = models.BooleanField(default=False)
    speed = models.PositiveIntegerField()
    asn = models.PositiveIntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)

    ixf_state = models.CharField(
        max_length=255, default="active", choices=django_ixctl.enum.MEMBER_STATE
    )
    ixf_member_type = models.CharField(
        max_length=255, choices=django_ixctl.enum.IXF_MEMBER_TYPE, default="peering"
    )

    class PdbRef(PdbRefModel.PdbRef):
        pdbctl = pdbctl.NetworkIXLan

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

        - pdb_object (`fullctl.service_bridge.pdbctl.NetworkIXLan`): netixlan instance
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

    @classmethod
    def preload_as_macro(cls, queryset):
        asns = {member.asn for member in queryset}
        if not asns:
            return queryset
        asn_map = {}
        for net in sot.ASSet().objects(asns=list(asns)):
            asn_map[net.asn] = net
        for member in queryset:
            member._net = asn_map.get(member.asn)
            yield member

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

        return get_as_set(self.as_macro)
        # return [as_set.strip() for as_set in re.split(r"[, ]+", self.as_macro)]

    @property
    def as_macro(self):
        if self.as_macro_override:
            return self.as_macro_override

        if self.net:
            if self.net.source == "peerctl":
                return self.net.as_set
            elif self.net.source == "pdbctl":
                return self.net.irr_as_set
        return ""

    @property
    def net(self):
        if hasattr(self, "_net"):
            return self._net

        self._net = sot.ASSet().first(asn=self.asn)
        return self._net

    def __str__(self):
        return f"AS{self.asn} - {self.ipaddr4} - {self.ipaddr6} ({self.id})"


@reversion.register
@grainy_model(
    namespace="rs",
    namespace_instance=(
        "routeserver.{instance.org.permission_id}.{instance.ix_id}.{instance.asn}"
    ),
)
class Routeserver(HandleRefModel):

    """
    Describes a routeserver at an internet exchange
    """

    ix = models.ForeignKey(
        InternetExchange,
        on_delete=models.CASCADE,
        related_name="rs_set",
    )

    # RS Config

    name = models.CharField(
        max_length=255,
        help_text=_("Routeserver name"),
    )

    asn = ASNField(help_text=_("ASN"))

    router_id = InetAddressField(
        store_prefix_length=False,
        help_text=_("Router Id"),
    )

    rpki_bgp_origin_validation = models.BooleanField(default=False)

    # ARS Config

    ars_type = models.CharField(
        max_length=32,
        choices=django_ixctl.enum.ARS_TYPES,
        default="bird",
    )

    max_as_path_length = models.IntegerField(
        default=32,
        help_text=_("Max length of AS_PATH attribute."),
    )

    no_export_action = models.CharField(
        max_length=8,
        choices=django_ixctl.enum.ARS_NO_EXPORT_ACTIONS,
        default="pass",
        help_text=_("RFC1997 well-known communities (NO_EXPORT and NO_ADVERTISE)"),
    )

    graceful_shutdown = models.BooleanField(
        default=False,
        help_text=_("Graceful BGP session shutdown"),
    )

    extra_config = models.TextField(
        null=True, blank=True, help_text=_("Extra arouteserver config")
    )

    class Meta:
        db_table = "ixctl_rs"
        unique_together = (("ix", "router_id"), ("ix", "name"))

    class HandleRef:
        tag = "routeserver"

    @property
    def org(self):
        return self.ix.instance.org

    @property
    def display_name(self):
        return self.name

    @property
    def routeserver_config(self):
        """
        Return the routeserver_config instance for this routeserver

        Will create the routeserver_config instance if it does not exist yet
        """
        if not hasattr(self, "_routeserver_config"):
            routeserver_config, created = RouteserverConfig.objects.get_or_create(
                routeserver=self
            )
            self._routeserver_config = routeserver_config
        return self._routeserver_config

    @property
    def routeserver_config_status_dict(self):
        """
        Returns a status dict for the current state of this routeserver's
        configuration
        """

        routeserver_config = self.routeserver_config

        task = routeserver_config.task

        # no status

        if not task and not routeserver_config.rs_response:
            return {"status": None}

        if not task:
            return routeserver_config.rs_response

        if task.status == "pending":
            return {"status": "queued"}
        if task.status == "running":
            return {"status": "generating"}
        if task.status == "cancelled":
            return {"status": "canceled"}
        if task.status == "failed":
            return {"status": "error", "error": task.error}
        if task.status == "completed":
            if not routeserver_config.rs_response:
                return {"status": "generated"}
            return routeserver_config.rs_response

        return {"status": None}

    @property
    def routeserver_config_status(self):
        return self.routeserver_config_status_dict.get("status")

    @property
    def routeserver_config_response(self):
        return self.routeserver_config.rs_response

    @property
    def routeserver_config_error(self):
        return self.routeserver_config_status_dict.get("error")

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
                "rfc1997_wellknown_communities": {
                    "policy": self.no_export_action,
                },
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
        Generate and return `dict` for ARouteserver clients config
        """

        asns = []
        asn_as_sets = {}
        clients = {}

        # TODO
        # where to get ASN sets from ??
        # peeringdb network ??
        rs_peers = InternetExchangeMember.preload_as_macro(
            self.ix.member_set.filter(is_rs_peer=True)
        )

        for member in rs_peers:
            if member.asn not in asns:
                asns.append(member.asn)
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

        # these aren't needed since they're already defined from SoT in the
        # more specific members list
        #
        # if asns:
        #     for net in pdbctl.Network().objects(asns=asns):
        #         if net.irr_as_set:
        #             asn_as_sets[f"AS{net.asn}"] = {
        #                 "as_sets": get_as_set(net.irr_as_set)
        #             }

        return {"asns": asn_as_sets, "clients": list(clients.values())}

    def __str__(self):
        return f"Routeserver {self.name} AS{self.asn}"


@reversion.register
class RouteserverConfig(HandleRefModel):

    """
    Describes a configuration (aroutserver generated) for a
    `Routeserver` instance
    """

    routeserver = models.OneToOneField(
        Routeserver,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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

    rs_response = models.JSONField(
        help_text=("Routeserver response"), null=True, blank=True
    )

    task = models.ForeignKey(
        "django_ixctl.RsConfGenerate",
        on_delete=models.CASCADE,
        related_name="routeserver_config_set",
        blank=True,
        null=True,
        help_text=_(
            "Reference to most recent generate task for this routeserver_config object"
        ),
    )

    class HandleRef:
        tag = "config.routeserver"

    class Meta:
        db_table = "ixctl_rsconf"

    @property
    def outdated(self):

        """
        Returns whether or not the config needs to be regenerated
        """

        # Route server has been updated since last generation,

        if not self.generated or self.generated < self.routeserver.updated:
            return True

        # RS Peer has been updated since last generation

        for member in self.routeserver.ix.member_set.filter(is_rs_peer=True):
            if self.generated < member.updated:
                return True
        return False

    def queue_generate(self):
        """
        Queue task to regenerate config
        """
        self.task = django_ixctl.models.tasks.RsConfGenerate.create_task(self.id)
        self.rs_response = {}
        self.save()

    def generate(self):

        """
        Generate the route server config using arouteserver
        """

        routeserver = self.routeserver
        ars_general = routeserver.ars_general
        ars_clients = routeserver.ars_clients

        config_dir = tempfile.mkdtemp(prefix="ixctl_routeserver_config")

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

        if routeserver.ars_type in ["bird", "bird2"]:
            ars_type = "bird"
        else:
            ars_type = routeserver.ars_type

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
        logger.debug(f"running command {cmd}")

        # TODO: bird v1 needs to generate
        # separate for each ip version
        #
        # how to store?

        if routeserver.ars_type == "bird":
            cmd += ["--ip-ver", "4"]
        elif routeserver.ars_type == "bird2":
            cmd += ["--target-version", "2.0.10"]

        process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        _, err = process.communicate(timeout=600)

        if process.returncode:
            if err:
                err = err.decode("utf-8")
                raise OSError(err)
            else:
                raise OSError(f"Process returned {process.returncode}")

        with open(outfile) as fh:
            self.body = f"# generated by ixctl at {datetime.now().isoformat()}\n"
            self.body += fh.read()

        self.save()


@reversion.register()
@grainy_model(
    namespace="net",
    namespace_instance="net.{instance.org.permission_id}.{instance.asn}",
)
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
        pdbctl = pdbctl.Network
        fields = {"asn": "pdb_id"}

    class HandleRef:
        tag = "net"

    class Meta:
        db_table = "ixctl_net"
        verbose_name_plural = _("Networks")
        verbose_name = _("Network")
        unique_together = (("instance", "asn"),)

    @classmethod
    def create_from_pdb(cls, instance, pdb_object, save=True, **fields):

        """
        create instance from peeringdb network

        Argument(s):

        - instance (`Instance`): instance that contains this network
        - pdb_object (`fullctl.service_bridge.pdbctl.Network`): pdb network
        - save (`bool`): if True commit to the database, otherwise dont

        Keyword Argument(s):

        Any arguments passed will be used to set properties on the
        object before creation

        Returns:

        - `Network` instance
        """

        net = super().create_from_pdb(
            pdb_object,
            save=save,
            instance=instance,
            name=pdb_object.name,
            asn=pdb_object.asn,
            **fields,
        )

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
                member for member in InternetExchangeMember.objects.filter(asn=self.asn)
            ]
        return self._members

    def __str__(self):
        return f"{self.name} (AS{self.asn})"
