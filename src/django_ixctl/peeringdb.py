from django_ixctl import models


def import_org(pdb_org, instance):
    return {
        "exchanges": import_exchanges(pdb_org, instance),
    }


def import_exchanges(pdb_org, instance):
    """
    Import all exchanges for the specified peeringdb org
    into specified ixctl org instance

    Argument(s):

    - pdb_org (`django_peeringdb.Organization`)
    - instance (`Instance`)

    Returns:

    - `list`: list of `InternetExchange` objects
    """

    exchanges = []
    cls = models.InternetExchange
    for ix in pdb_org.ix_set.filter(status="ok"):
        exchanges.append(import_exchange(ix, instance))
    return exchanges


def import_exchange(pdb_ix, instance):

    """
    Import the specified peeringdb exchange into the
    specified ixctl org instance

    Argument(s)

    - pdb_ix (`django_peeringdb.IXLan`)
    - instance (`Instance`)

    Returns:

    - `InternetExchange`
    """

    qset = models.InternetExchange.objects.filter(instance=instance, pdb_id=pdb_ix.id)
    if qset.exists():
        return
    return models.InternetExchange.create_from_pdb(instance, pdb_ix.ixlan_set.first(),)


def get_as_set(pdb_net):

    """
    Check the irr_as_net on a peeringdb network and return the
    as set value with the source specification stripped out

    Argument(s):

    - pdb_net (`django_peeringdb.Network`)

    Returns:

    - `str`
    """

    as_set = pdb_net.irr_as_set
    if as_set and "::" in as_set:
        as_set = as_set.split("::")[1]
    elif as_set and "@" in as_set:
        as_set = as_set.split("@")[0]
    return as_set
