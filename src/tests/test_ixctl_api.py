import json
from django.urls import reverse
from django.contrib.auth import get_user_model

import django_ixctl.models as models


def test_ix_import_peeringdb(db, pdb_data, account_objects):
    org = account_objects.org

    client = account_objects.api_client
    response = client.post(
        reverse("ixctl_api:ix-import-peeringdb", args=(org.slug,)), {"pdb_ix_id": 239}
    )
    data = response.json()
    assert response.status_code == 200
    assert data["data"][0]["pdb_id"] == 239


def test_ix_list(db, pdb_data, account_objects):

    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(reverse("ixctl_api:ix-list", args=(org.slug,)))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["pdb_id"] == ix.pdb_id
    assert data[0]["urlkey"] == ix.urlkey
    assert data[0]["name"] == ix.pdb.ix.name
    assert data[0]["id"] == ix.id
    assert data[0]["status"] == ix.status


def test_ix_retrieve(db, pdb_data, account_objects):

    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(reverse("ixctl_api:ix-detail", args=(org.slug, ix.id)))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["pdb_id"] == ix.pdb_id
    assert data[0]["urlkey"] == ix.urlkey
    assert data[0]["name"] == ix.pdb.ix.name
    assert data[0]["id"] == ix.id
    assert data[0]["status"] == ix.status

def test_ix_create(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org
    
    data = {
        "name": "test IX new"
    }
    response = client.post(
        reverse("ixctl_api:ix-list", args=(org.slug,)),
        json.dumps(data),
        content_type="application/json"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["pdb_id"] == None
    assert data[0]["name"] == "test IX new"
    assert models.InternetExchange.objects.filter(name="test IX new").exists()

def test_ix_members(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.get(reverse("ixctl_api:ix-members", args=(org.slug, ix.id)))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["pdb_id"] == ixmember.pdb_id
    assert data[0]["id"] == ixmember.id
    assert data[0]["status"] == ixmember.status
    assert data[0]["ixf_member_type"] == ixmember.ixf_member_type
    assert data[0]["ixf_state"] == ixmember.ixf_state
    assert data[0]["display_name"] == ixmember.display_name
    assert data[0]["ipaddr4"] == ixmember.ipaddr4
    assert data[0]["ipaddr6"] == ixmember.ipaddr6
    assert data[0]["is_rs_peer"] == ixmember.is_rs_peer
    assert data[0]["speed"] == ixmember.speed


def test_ix_delete_member(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.delete(
        reverse("ixctl_api:ix-member", args=(org.slug, ix.id, ixmember.id)),
    )

    assert response.status_code == 200

    assert (
        models.InternetExchangeMember.objects.filter(id=ixmember.id).exists() == False
    )


def test_ix_add_member(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.post(
        reverse("ixctl_api:ix-members", args=(org.slug, ix.id)),
        json.dumps(
            {
                "asn": 63311,
                "ixf_state": "active",
                "ixf_member_type": "peering",
                "name": "",
                "ippadr4": "206.41.111.20",
                "ipaddr6": "2001:504:41:111::20",
                "speed": 1000,
                "is_rs_peer": False,
            }
        ),
        content_type="application/json",
    )

    data = response.json()["data"]
    assert response.status_code == 200

    assert models.InternetExchangeMember.objects.filter(id=data[0]["id"]).exists()


def test_ix_edit_member(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.put(
        reverse("ixctl_api:ix-member", args=(org.slug, ixmember.ix.id, ixmember.id)),
        json.dumps(
            {
                "id": ixmember.id,
                "ix": ixmember.ix.id,
                "asn": 63311,
                "ixf_state": "active",
                "ixf_member_type": "peering",
                "name": "override",
                "ipaddr4": "206.41.111.20",
                "ipaddr6": "2001:504:41:111::20",
                "speed": 1000,
                "is_rs_peer": False,
            }
        ),
        content_type="application/json",
    )
    data = response.json()["data"]
    assert response.status_code == 200

    ixmember.refresh_from_db()
    assert ixmember.name == "override"
    assert ixmember.ipaddr4 == "206.41.111.20"
    assert ixmember.ipaddr6 == "2001:504:41:111::20"


def test_list_routeservers(db, pdb_data, account_objects):
    ix = account_objects.ix
    rs = account_objects.routeserver
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(reverse("ixctl_api:ix-routeservers", args=(org.slug, ix.id)))
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == ix.rs_set.count()
    assert data[0]["name"] == ix.rs_set.first().name

def test_create_routeserver(db, pdb_data, account_objects):
    ix = account_objects.ix
    rs = account_objects.routeserver
    client = account_objects.api_client
    org = account_objects.org

    payload = {
        'asn': 63311,
        'graceful_shutdown': False,
        'ix': 1,
        'max_as_path_length': 32,
        'name': 'New rs',
        'no_export_action': 'pass',
        'router_id': '194.168.0.1',
    }
    response = client.post(
        reverse("ixctl_api:ix-routeservers", args=(org.slug, ix.id)),
        json.dumps(payload),
        content_type="application/json"
    )

    # Response is correct
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "New rs"
    assert data[0]["router_id"] == "194.168.0.1"

    # Changes are persisted to db
    assert models.Routeserver.objects.filter(id=data[0]["id"]).exists()
    new_rs = models.Routeserver.objects.filter(id=data[0]["id"]).first()
    assert new_rs.name == "New rs"
    ix.refresh_from_db()
    assert ix.rs_set.count() == 2


def test_delete_routeserver(db, pdb_data, account_objects):
    ix = account_objects.ix
    rs = account_objects.routeserver
    client = account_objects.api_client
    org = account_objects.org
    response = client.delete(
        reverse("ixctl_api:ix-routeserver", args=(org.slug, ix.id, rs.id)),
        content_type="application/json"
    )

    assert response.status_code == 200
    # Response is correct
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "test routeserver"
    assert data[0]["router_id"] == "192.168.0.1"

    # Changes are persisted to db
    assert not models.Routeserver.objects.filter(id=rs.id).exists()


def test_update_routeserver(db, pdb_data, account_objects):
    ix = account_objects.ix
    rs = account_objects.routeserver
    client = account_objects.api_client
    org = account_objects.org
    payload = {
        'ars_type': 'bird',
        'asn': 63311,
        'graceful_shutdown': False,
        'id': 1,
        'ix': 1,
        'max_as_path_length': 32,
        'name': 'changed name', #changed
        'no_export_action': 'pass',
        'router_id': '193.168.0.1', #changed
        'rpki_bgp_origin_validation': False,
        'status': 'ok',
    }
    response = client.put(
        reverse("ixctl_api:ix-routeserver", args=(org.slug, ix.id, rs.id)),
        json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200
    # Response is correct
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "changed name"
    assert data[0]["router_id"] == "193.168.0.1"

    # Changes are persisted to db
    routeserver = models.Routeserver.objects.filter(id=rs.id).first()
    assert routeserver.name == "changed name"
    assert str(routeserver.router_id) == "193.168.0.1"

    # Unchanged fields remain unchanged
    assert data[0]["ars_type"] == routeserver.ars_type



def test_retrieve_routeserverconfig():
    assert 0 

def test_retrieve_routeserverconfig_plain():
    assert 0

def test_list_users(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(reverse("ixctl_api:user-list", args=(org.slug,)))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == get_user_model().objects.count()
    assert set([d["name"] for d in data]) == set([
        f"{user.first_name} {user.last_name}" for user in get_user_model().objects.all()
    ])

def test_list_orgs(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(reverse("ixctl_account_api:org-list"))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == len(account_objects.orgs)
    assert set([d["name"] for d in data]) == set([
        org.display_name for org in account_objects.orgs
    ])
