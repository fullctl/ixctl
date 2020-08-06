import django_ixctl.models as models
import django_peeringdb.models.concrete as pdb_models
 
# def test_network_create_from_pdb(db, pdb_data, account_objects):

#     net = models.Network.create_from_pdb(
#         account_objects.ixctl_instance, account_objects.pdb_net,
#     )

#     assert net.asn == account_objects.pdb_net.asn
#     assert net.pdb_id == account_objects.pdb_net.id
#     assert net.pdb == account_objects.pdb_net


# def test_network_display_name(db, pdb_data, account_objects):

#     net = models.Network.create_from_pdb(
#         account_objects.ixctl_instance, account_objects.pdb_net
#     )

#     assert net.display_name == account_objects.pdb_net.name
#     net.name = "override"
#     assert net.display_name == "override"


# def test_network_require(db, pdb_data, account_objects):

#     pdb_net = models.pdb_models.Network.objects.get(id=20)
#     net = models.Network.require(
#         account_objects.ixctl_instance, account_objects.pdb_net.asn, name="override"
#     )

#     assert net.name == "override"
#     assert net.asn == account_objects.pdb_net.asn
#     assert net.pdb_id == account_objects.pdb_net.id

#     net_b = models.Network.require(
#         account_objects.ixctl_instance, account_objects.pdb_net.asn,
#     )

#     assert net.id == net_b.id

#     net_c = models.Network.require(account_objects.ixctl_instance, 33333)

#     assert net_c.asn == 33333
#     assert net_c.name == "AS33333"


def test_ix(db, pdb_data, account_objects):
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )

    assert ix.pdb_id == account_objects.pdb_ixlan.id
    assert ix.pdb == account_objects.pdb_ixlan


# def test_portinfo(db, pdb_data, account_objects):

#     net = models.Network.create_from_pdb(
#         account_objects.ixctl_instance, account_objects.pdb_net
#     )

#     ix = models.InternetExchange.create_from_pdb(
#         account_objects.ixctl_instance, account_objects.pdb_ixlan
#     )

#     netixlan = models.pdb_models.NetworkIXLan.objects.filter(ixlan_id=239).first()

#     portinfo = models.PortInfo.create_from_pdb(netixlan, ix, net)

#     assert portinfo.pdb_id == netixlan.id
#     assert portinfo.pdb == netixlan

#     assert portinfo.net_name == netixlan.net.name
#     assert portinfo.display_name == netixlan.net.name

#     portinfo.name = "override"
#     assert portinfo.display_name == "override"
