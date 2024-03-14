"""
Logic to sync ixctl to netbox

Syncs the following information

InternetExchange.mtu -> netbox.ipam.VLAN.interfaces.mtu matching by ix.vlan_id to VLAN.id
InternetExchangePrefix.prefix -> netbox.ipam.VLAN.prefixes where ix.vlan_id matches VLAN.id
InternetExchangeMember.mac_address -> netbox.
"""

import fullctl.service_bridge.netbox as netbox
import structlog
from fullctl.django.models.concrete import Organization

from django_ixctl.models.ixctl import (
    InternetExchange,
    InternetExchangeMember,
    InternetExchangePrefix,
)

log = structlog.get_logger("django")


def vlan_interfaces(vlan: netbox.VLANObject):
    """
    yields device interfaces for the specified vlan
    """

    interfaces = netbox.Interface().objects()
    for interface in interfaces:
        if interface.untagged_vlan and interface.untagged_vlan.id == vlan.id:
            yield interface
        elif interface.tagged_vlans and vlan.id in [
            v["id"] for v in interface.tagged_vlans
        ]:
            yield interface


def push_exchanges(org: Organization, ix_slug: str = None):
    """
    Pushes all exchanges to netbox
    """

    qset = InternetExchange.objects.filter(instance__org=org)

    if ix_slug:
        log.info(f"Limiting to exchange {ix_slug}", org=org.slug)
        qset = qset.filter(slug=ix_slug)

    for ix in qset:
        push_exchange(ix)


def push_exchange(exchange: InternetExchange):
    """
    Pushes exchange to netbox
    """

    log.info(
        f"Pushing exchange {exchange.slug} to netbox", org=exchange.instance.org.slug
    )

    vlan = netbox.VLAN().first(vid=exchange.vlan_id)
    if not vlan:
        log.warning(
            f"VLAN {exchange.vlan_id} not found in netbox, skipping",
            org=exchange.instance.org.slug,
        )
        return

    push_vlan(vlan, exchange)


def push_vlan(vlan: netbox.VLANObject, exchange: InternetExchange):
    """
    Pushes the specified vlan to netbox
    """

    for interface in vlan_interfaces(vlan):
        log.info(
            f"Setting MTU for interface {interface.name} to {exchange.mtu}",
            org=exchange.instance.org.slug,
            vlan_id=vlan.vid,
        )
        netbox.Interface().partial_update(interface, {"mtu": exchange.mtu})

    push_prefixes(vlan, exchange)
    push_members(vlan, exchange)


def push_prefixes(vlan: netbox.VLANObject, exchange: InternetExchange):
    """
    Pushes the prefixes for the specified exchange to netbox
    """

    for prefix in exchange.prefixes.all():
        push_prefix(vlan, prefix)

    push_prefix_deletions(vlan, exchange)


def push_prefix(vlan: netbox.VLANObject, prefix: InternetExchangePrefix):
    """
    Pushes the specified prefix to netbox
    """

    # does netbox prefix already exist?
    nb_prefix = netbox.Prefix().first(prefix=str(prefix.prefix))

    if not nb_prefix:
        log.info(
            f"Creating prefix {prefix.prefix} for vlan {vlan.vid}",
            org=prefix.ix.instance.org.slug,
        )

        netbox.Prefix().create(
            {"vlan": vlan.id, "prefix": str(prefix.prefix), "status": "active"}
        )
    else:
        log.info(
            f"Prefix {prefix.prefix} already exists for vlan {vlan.vid}",
            org=prefix.ix.instance.org.slug,
        )


def push_prefix_deletions(vlan: netbox.VLANObject, exchange: InternetExchange):
    """
    Pushes the deletions of prefixes for the specified exchange to netbox
    """

    nb_prefixes = netbox.Prefix().objects(vlan_id=vlan.id)

    for nb_prefix in nb_prefixes:
        if nb_prefix.prefix not in [str(p.prefix) for p in exchange.prefixes.all()]:
            log.info(
                f"Deleting prefix {nb_prefix.prefix} for vlan {vlan.vid}",
                org=exchange.instance.org.slug,
            )
            netbox.Prefix().destroy(nb_prefix)


def push_members(vlan: netbox.VLANObject, exchange: InternetExchange):
    """
    Pushes the members for the specified exchange to netbox
    """

    # filter(macaddr__isnull=False).exclude(macaddr="")
    for member in exchange.member_set.all():
        push_member(vlan, member)


def push_member(vlan: netbox.VLANObject, member: InternetExchangeMember):
    """
    Pushes the specified member to netbox
    """

    nb_ip4 = netbox.IPAddress().first(address=str(member.ipaddr4))
    nb_ip6 = netbox.IPAddress().first(address=str(member.ipaddr6))

    if not nb_ip4 and not nb_ip6:
        log.warning(
            f"Netbox ip address not found for member {member.name}",
            org=member.ix.instance.org.slug,
            ip4=member.ipaddr4,
            ip6=member.ipaddr6,
            asn=member.asn,
        )
        return

    nb_interface4 = (
        netbox.Interface().first(ip4=nb_ip4.assigned_object_id) if nb_ip4 else None
    )
    nb_interface6 = (
        netbox.Interface().first(ip6=nb_ip6.assigned_object_id) if nb_ip6 else None
    )

    if not nb_interface4 and not nb_interface6:
        log.warning(
            f"Netbox interface not found for member {member.name}",
            org=member.ix.instance.org.slug,
            ip4=member.ipaddr4,
            ip6=member.ipaddr6,
            asn=member.asn,
        )
        return

    if nb_interface4:
        log.info(
            f"Setting MAC address for interface {nb_interface4.name} to {member.macaddr}",
            org=member.ix.instance.org.slug,
            ip4=member.ipaddr4,
            macaddr=member.macaddr,
        )
        nb_interface4.mac_address = member.macaddr
        netbox.Interface().partial_update(
            nb_interface4, {"mac_address": str(member.macaddr)}
        )

    if nb_interface6:
        log.info(
            f"Setting MAC address for interface {nb_interface6.name} to {member.macaddr}",
            org=member.ix.instance.org.slug,
            ip6=member.ipaddr6,
            macaddr=member.macaddr,
        )
        nb_interface6.mac_address = member.macaddr
        netbox.Interface().partial_update(
            nb_interface6, {"mac_address": str(member.macaddr)}
        )


def push(org: Organization, ix_slug: str = None):
    """
    pushes to netbox
    """
    push_exchanges(org, ix_slug=ix_slug)


def pull():
    """
    pulls from netbox
    """
    pass
