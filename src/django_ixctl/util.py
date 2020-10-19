from django.conf import settings
import django_peeringdb.models.concrete as pdb_models
from django_ixctl.auth import permissions
from django_ixctl.models import (
    Instance,
    Organization,
    OrganizationUser,
    APIKey,
    Network,
)




def verified_asns(perms):
    verified_asns = []
    for verified_asn in perms.pset.expand("verified.asn.?", explicit=True, exact=True):
        asn = verified_asn.keys[-1]
        try:
            pdb_net = pdb_models.Network.objects.get(asn=asn)
        except (ValueError, pdb_models.Network.DoesNotExist):
            pdb_net = None

        verified_asns.append({
            "asn": asn,
            "pdb_net": pdb_net
        })

    return verified_asns

def create_networks_from_verified_asns(user):

    try:
        instance = user.org_set.filter(org__personal=True).first().org.instance
    except AttributeError:
        # users that dont have an org (manually created superusers)
        return

    perms = permissions(user)
    perms.load()


    asns = [
        namespace[2] for namespace in
        perms.pset.expand("verified.asn.?.?", exact=True, explicit=True)
    ]

    for asn in asns:

        try:
            asn = int(asn)
        except ValueError:
            continue

        if not Network.objects.filter(instance=instance, asn=asn).exists():
            try:
                pdb_net = pdb_models.Network.objects.get(asn=asn)
                Network.create_from_pdb(instance, pdb_net)
            except pdb_models.Network.DoesNotExist:
                Network.objects.create(
                    name=f"AS{asn}",
                    asn=asn,
                    instance=instance
                )

def create_personal_org(user):

    if not settings.MANAGED_BY_OAUTH:

        # organizations are not managed by oauth
        # so for now we just ensure that each user
        # has a personal org

        if user.is_authenticated:

            org, _ = Organization.objects.get_or_create(
                name=f"{user.username} personal org",
                slug=user.username,
                personal=True,
            )

            instance = Instance.get_or_create(org)

            OrganizationUser.objects.create(
                org=org, user=user,
            )

            user.grainy_permissions.add_permission(f"*.{org.id}", "crud")
            return org
    return

