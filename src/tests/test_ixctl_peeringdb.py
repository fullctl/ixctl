import django_ixctl.models as models
from django_ixctl import peeringdb
from fullctl.service_bridge.pdbctl import InternetExchange, Network


def test_import_exchange(db, pdb_data, account_objects):
    pdb_ix = InternetExchange().object(239)
    ix = peeringdb.import_exchange(pdb_ix, account_objects.ixctl_instance)

    assert isinstance(ix, models.InternetExchange)
    assert ix.name == pdb_ix.name
    assert ix.pdb_id == pdb_ix.id


def test_get_as_set(db, pdb_data, account_objects):
    pdb_net = Network().object(20)
    pdb_net.irr_as_set = "foo::bar"
    assert peeringdb.get_as_set(pdb_net) == "bar"
    pdb_net.irr_as_set = "foo@bar"
    assert peeringdb.get_as_set(pdb_net) == "foo"
