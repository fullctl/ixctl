from django_ixctl import models


def import_org(pdb_org, instance):
    return {
        "exchanges": import_exchanges(pdb_org, instance),
    }


def import_exchanges(pdb_org, instance):
    exchanges = []
    cls = models.InternetExchange
    for ix in pdb_org.ix_set.filter(status="ok"):
        exchanges.append(import_exchange(ix, instance))
    return exchanges


def import_exchange(pdb_ix, instance):
    qset = models.InternetExchange.objects.filter(instance=instance, pdb_id=pdb_ix.id)
    if qset.exists():
        return
    return models.InternetExchange.create_from_pdb(instance, pdb_ix.ixlan_set.first(),)


def get_as_set(pdb_net):
    as_set = pdb_net.irr_as_set
    if as_set and "::" in as_set:
        as_set = as_set.split("::")[1]
    elif as_set and "@" in as_set:
        as_set = as_set.split("@")[0]
    return as_set
