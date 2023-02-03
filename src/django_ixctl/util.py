import fullctl.service_bridge.pdbctl as pdbctl
from fullctl.django.auth import permissions

from django_ixctl.models import Network


def create_networks_from_verified_asns(user):
    try:
        instance = user.org_set.filter(org__personal=True).first().org.instance
    except AttributeError:
        # users that dont have an org (manually created superusers)
        return

    perms = permissions(user)
    perms.load()

    asns = [
        namespace[2]
        for namespace in perms.pset.expand(
            "verified.asn.?.?", exact=True, explicit=True
        )
    ]

    for asn in asns:
        try:
            asn = int(asn)
        except ValueError:
            continue

        if not Network.objects.filter(instance=instance, asn=asn).exists():
            pdb_net = pdbctl.Network().first(asn=asn)
            if pdb_net:
                Network.create_from_pdb(instance, pdb_net)
            else:
                Network.objects.create(name=f"AS{asn}", asn=asn, instance=instance)
