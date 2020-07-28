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
