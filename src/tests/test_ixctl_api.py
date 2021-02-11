import json

from django.urls import reverse

import django_ixctl.models as models


def test_ix_import_peeringdb(db, pdb_data, account_objects):
    org = account_objects.org

    client = account_objects.api_client

    response = client.post(
        reverse("ixctl_api:ix-import-peeringdb", args=(org.slug,)),
        {"pdb_ix_id": 239},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"][0]["pdb_id"] == 239


def test_ix_import_peeringdb_invalid(db, pdb_data, account_objects):
    org = account_objects.org
    client = account_objects.api_client
    response = client.post(
        reverse("ixctl_api:ix-import-peeringdb", args=(org.slug,)),
        {"pdb_ix_id": 10000000000000},
    )
    assert response.status_code == 400
    data = response.json()
    assert "Unknown peeringdb organization" in data["errors"]["pdb_ix_id"]


def test_ix_import_peeringdb_reimport(db, pdb_data, account_objects):
    org = account_objects.org
    client = account_objects.api_client
    client.post(
        reverse("ixctl_api:ix-import-peeringdb", args=(org.slug,)), {"pdb_ix_id": 239}
    )
    response = client.post(
        reverse("ixctl_api:ix-import-peeringdb", args=(org.slug,)), {"pdb_ix_id": 239}
    )
    assert response.status_code == 400
    data = response.json()
    assert "You have already imported this exchange" in data["errors"]["pdb_ix_id"]


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

    response = client.get(reverse("ixctl_api:ix-detail", args=(org.slug, ix.slug)))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["pdb_id"] == ix.pdb_id
    assert data[0]["urlkey"] == ix.urlkey
    assert data[0]["name"] == ix.pdb.ix.name
    assert data[0]["id"] == ix.id
    assert data[0]["status"] == ix.status


def test_ix_create(db, pdb_data, account_objects):
    client = account_objects.api_client
    org = account_objects.org

    data = {"name": "test IX new"}
    response = client.post(
        reverse("ixctl_api:ix-list", args=(org.slug,)),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["pdb_id"] is None
    assert data[0]["name"] == "test IX new"
    assert models.InternetExchange.objects.filter(name="test IX new").exists()


def test_ix_put_ixf_export_policy(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    assert ix.ixf_export_privacy == "public"

    data = {
        "name": ix.name,
        "pdb_id": ix.pdb_id,
        "urlkey": "new url key",
        "slug": ix.slug,
        "ixf_export_privacy": "private",
    }

    response = client.put(
        reverse(
            "ixctl_api:ix-detail",
            args=(
                org.slug,
                ix.slug,
            ),
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    output = response.json()["data"]
    assert len(output) == 1

    ix.refresh_from_db()
    assert ix.ixf_export_privacy == data["ixf_export_privacy"]
    assert ix.urlkey == data["urlkey"]


def test_ix_put_slug(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    data = {
        "name": ix.name,
        "pdb_id": ix.pdb_id,
        "urlkey": ix.urlkey,
        "slug": "changed-slug",
    }
    response = client.put(
        reverse(
            "ixctl_api:ix-detail",
            args=(
                org.slug,
                ix.slug,
            ),
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    output = response.json()["data"]
    assert len(output) == 1

    ix.refresh_from_db()
    assert ix.slug == data["slug"]

    assert output[0]["slug"] == data["slug"]
    assert output[0]["name"] == data["name"]
    assert output[0]["pdb_id"] == data["pdb_id"]


def test_ix_put_slug_invalid(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    data = {
        "name": ix.name,
        "pdb_id": ix.pdb_id,
        "urlkey": ix.urlkey,
        "slug": "invalid slug",
    }
    response = client.put(
        reverse(
            "ixctl_api:ix-detail",
            args=(
                org.slug,
                ix.slug,
            ),
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "slug" in list(response.json()["errors"].keys())


def test_ix_create_invalid(db, pdb_data, account_objects):
    client = account_objects.api_client
    org = account_objects.org

    data = {"name": None}
    response = client.post(
        reverse("ixctl_api:ix-list", args=(org.slug,)),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["errors"] == {"name": ["This field may not be null."]}


def test_ix_members(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.get(reverse("ixctl_api:member-list", args=(org.slug, ix.slug)))

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
        reverse("ixctl_api:member-detail", args=(org.slug, ix.slug, ixmember.id)),
        content_type="application/json",
    )
    assert response.status_code == 200

    assert (
        models.InternetExchangeMember.objects.filter(id=ixmember.id).exists() is False
    )


def test_ix_create_member(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    response = client.post(
        reverse("ixctl_api:member-list", args=(org.slug, ix.slug)),
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


def test_ix_create_member_invalid(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.post(
        reverse("ixctl_api:member-list", args=(org.slug, ix.slug)),
        json.dumps(
            {
                "asn": 63311,
                "ixf_state": "active",
                "ixf_member_type": "peering",
                "name": "",
                "ippadr4": None,
                "ipaddr6": ixmember.ipaddr6,
                "speed": 1000,
                "is_rs_peer": False,
            }
        ),
        content_type="application/json",
    )
    errors = response.json()["errors"]
    assert response.status_code == 400
    assert errors == {
        "non_field_errors": ["IPv6 address exists already in this exchange"]
    }


def test_ix_edit_member(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.put(
        reverse("ixctl_api:member-detail", args=(org.slug, ix.slug, ixmember.id)),
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
    assert response.status_code == 200

    ixmember.refresh_from_db()
    assert ixmember.name == "override"
    assert ixmember.ipaddr4 == "206.41.111.20"
    assert ixmember.ipaddr6 == "2001:504:41:111::20"


def test_ix_edit_member_invalid(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    ixmember = ix.member_set.first()

    response = client.put(
        reverse("ixctl_api:member-detail", args=(org.slug, ix.slug, ixmember.id)),
        json.dumps(
            {
                "id": ixmember.id,
                "ix": ixmember.ix.id,
                "asn": 63311,
                "ixf_state": "active",
                "ixf_member_type": "peering",
                "name": "override",
                "ipaddr4": "",
                "ipaddr6": "",
                "speed": 1000,
                "is_rs_peer": False,
            }
        ),
        content_type="application/json",
    )
    errors = response.json()["errors"]
    assert response.status_code == 400
    assert errors == {
        "ipaddr4": ["Input required for IPv4 or IPv6"],
        "ipaddr6": ["Input required for IPv4 or IPv6"],
    }


def test_list_routeservers(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org
    assert account_objects.routeserver
    response = client.get(reverse("ixctl_api:rs-list", args=(org.slug, ix.slug)))
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == ix.rs_set.count()
    assert data[0]["name"] == ix.rs_set.first().name


def test_create_routeserver(db, pdb_data, account_objects):
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org
    assert account_objects.routeserver
    payload = {
        "asn": 63311,
        "graceful_shutdown": False,
        "ix": 1,
        "max_as_path_length": 32,
        "name": "New rs",
        "no_export_action": "pass",
        "router_id": "194.168.0.1",
    }
    response = client.post(
        reverse("ixctl_api:rs-list", args=(org.slug, ix.slug)),
        json.dumps(payload),
        content_type="application/json",
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
        reverse("ixctl_api:rs-detail", args=(org.slug, ix.slug, rs.id)),
        content_type="application/json",
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
        "ars_type": "bird",
        "asn": 63311,
        "graceful_shutdown": False,
        "id": 1,
        "ix": 1,
        "max_as_path_length": 32,
        "name": "changed name",  # changed
        "no_export_action": "pass",
        "router_id": "193.168.0.1",  # changed
        "rpki_bgp_origin_validation": False,
        "status": "ok",
    }
    response = client.put(
        reverse("ixctl_api:rs-detail", args=(org.slug, ix.slug, rs.id)),
        json.dumps(payload),
        content_type="application/json",
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


def test_retrieve_routeserverconfig(db, pdb_data, account_objects):
    rs = account_objects.routeserver
    rsconf = rs.rsconf
    rsconf.generate()
    ix = account_objects.ix
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(
        reverse("ixctl_api:rsconf-detail", args=(org.slug, ix.slug, rs.name))
    )
    assert response.status_code == 200

    response_plain = client.get(
        reverse("ixctl_api:rsconf-plain", args=(org.slug, ix.slug, rs.name))
    )
    assert response_plain.status_code == 200
