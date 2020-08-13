import django_ixctl.models as models
import django_peeringdb.models.concrete as pdb_models

from django_ixctl import peeringdb 

def test_import_exchange(db, pdb_data, account_objects):

    pdb_ix = pdb_models.InternetExchange.objects.first()

    ix = peeringdb.import_exchange(pdb_ix, account_objects.ixctl_instance)
    

    assert isinstance(ix, models.InternetExchange)
    assert ix.name == pdb_ix.name
    assert ix.pdb_id == pdb_ix.id


def test_import_exchange(db, pdb_data, account_objects):
    pdb_org = pdb_models.Organization.objects.first()
    print(pdb_org)
    assert 0 