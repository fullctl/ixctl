import django_ixctl.models as models
import django_peeringdb.models.concrete as pdb_models


def test_ix(db, pdb_data, account_objects):
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )

    assert ix.pdb_id == account_objects.pdb_ixlan.id
    assert ix.pdb == account_objects.pdb_ixlan


def test_ixmember(db, pdb_data, account_objects):

    net = account_objects.pdb_net
    netixlan = pdb_models.NetworkIXLan.objects.filter(ixlan_id=239).first()
    # The following line also runs the
    # create_from_pdb method of the InternetExchangeMember
    # corresonding to the IX.
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )

    ixmember = ix.member_set.first()
    assert ixmember.pdb_id == netixlan.id
    assert ixmember.pdb == netixlan

    assert ixmember.name == netixlan.net.name
    assert ixmember.display_name == netixlan.net.name

    ixmember.name = "override"
    assert ixmember.display_name == "override"
