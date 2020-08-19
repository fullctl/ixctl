import django_ixctl.models as models
import django_peeringdb.models.concrete as pdb_models

from django_ixctl import peeringdb 

def test_import_exchange(db, pdb_data, account_objects):
    pdb_ix = pdb_models.InternetExchange.objects.first()
    ix = peeringdb.import_exchange(pdb_ix, account_objects.ixctl_instance)

    assert isinstance(ix, models.InternetExchange)
    assert ix.name == pdb_ix.name
    assert ix.pdb_id == pdb_ix.id

def test_import_exchanges(db, pdb_data, account_objects):
    pdb_org = pdb_models.Organization.objects.filter(id=10843).first()
    exchanges = peeringdb.import_exchanges(pdb_org, account_objects.ixctl_instance)
    assert len(exchanges) == pdb_org.ix_set.count()
    for ix in exchanges:
        assert pdb_org.ix_set.filter(name=ix.name).exists()
        assert pdb_org.ix_set.filter(id=ix.pdb_id).exists()

def test_import_org(db, pdb_data, account_objects):
    pdb_org = pdb_models.Organization.objects.filter(id=10843).first()
    org = peeringdb.import_org(pdb_org, account_objects.ixctl_instance)
    assert len(org["exchanges"]) == pdb_org.ix_set.count()

def test_get_as_set(db, pdb_data, account_objects):
    pdb_net = pdb_models.Network.objects.first()
    pdb_net.irr_as_set = "foo::bar"
    assert peeringdb.get_as_set(pdb_net) == "bar"
    pdb_net.irr_as_set = "foo@bar"
    assert peeringdb.get_as_set(pdb_net) == "foo"
