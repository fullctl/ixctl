import json
from django.urls import reverse

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


def test_list_routeservers():
    assert 0

def test_create_routeserver():
    assert 0

def test_delete_routeserver():
    assert 0

def test_update_routeserver():
    assert 0

def test_retrieve_routeserverconfig():
    assert 0 

def test_retrieve_routeserverconfig_plain():
    assert 0

def test_list_users():
    assert 0

def test_list_orgs():
    assert 0