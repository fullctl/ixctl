import ipaddress
import json
import os

import django_peeringdb.models.concrete as pdb_models
import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

import django_ixctl.models as models


def test_pdb_create_error(db, pdb_data, account_objects):
    with pytest.raises(ValueError, match=r"^Expected .* instance$"):
        models.InternetExchange.create_from_pdb(
            account_objects.ixctl_instance, account_objects.pdb_ix
        )


def test_instance(db, pdb_data, account_objects):
    instance = account_objects.ixctl_instance
    assert instance.org == account_objects.org


def test_instance_create(db, pdb_data, account_objects):
    org = account_objects.orgs[1]
    instance = models.Instance.get_or_create(org)
    assert instance.org == org
    assert instance.org.status == "ok"


def test_ix(db, pdb_data, account_objects):
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )

    assert ix.pdb_id == account_objects.pdb_ixlan.id
    assert ix.pdb == account_objects.pdb_ixlan


def test_ix_display_name(db, pdb_data, account_objects):
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )

    assert ix.display_name == ix.name
    # ix.name = ''
    # ix.save()
    # assert ix.display_naars_typeme == ix.pdb_id

    # ix.pdb_id = None
    # ix.save()
    # assert ix.display_name.startswith("Nameless Exchange")


def test_ix_slug(db, pdb_data, account_objects):
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )
    assert (
        ix.slug == ix.name.replace("/", "_").replace(" ", "_").replace("-", "_").lower()
    )

    ix.slug = "new-slug"
    ix.full_clean()
    ix.save()
    assert ix.slug == "new-slug"

    # Slug cannot have spaces in it
    ix.slug = "new slug"
    with pytest.raises(ValidationError):
        ix.full_clean()


def test_ix_ixf_export_privacy(db, pdb_data, account_objects):
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )
    assert ix.ixf_export_privacy == "public"

    # option to change to private
    ix.ixf_export_privacy = "private"
    ix.save()
    assert ix.ixf_export_privacy == "private"

    # cannot change to other choices
    ix.ixf_export_privacy = "other"
    with pytest.raises(ValidationError):
        ix.full_clean()


def test_ix_ixf_export_url(db, pdb_data, account_objects):
    ix = models.InternetExchange.create_from_pdb(
        account_objects.ixctl_instance, account_objects.pdb_ixlan
    )

    path = reverse(
        "ixf export",
        args=(
            ix.instance.org.slug,
            ix.slug,
        ),
    )
    assert path == ix.ixf_export_url


def test_ixmember(db, pdb_data, account_objects):
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


def test_routeserver(db, pdb_data, account_objects):

    rs = account_objects.routeserver
    assert rs.ix == account_objects.ix
    assert rs.name == "test routeserver"
    assert rs.asn == account_objects.pdb_net.asn
    assert rs.router_id == ipaddress.IPv4Address("192.168.0.1")
    assert rs.rpki_bgp_origin_validation is False
    assert rs.ars_type == "bird"
    assert rs.max_as_path_length == 32
    assert rs.no_export_action == "pass"
    assert rs.graceful_shutdown is False
    assert rs.extra_config is None

    assert rs.display_name == rs.name
    assert (
        rs.__str__() == f"Routeserver test routeserver AS{account_objects.pdb_net.asn}"
    )


def test_routeserver_ars_general(db, pdb_data, account_objects):
    rs = account_objects.routeserver
    fn = os.path.join(
        os.path.dirname(__file__), "data", "rs", "ars_general_default.json"
    )
    with open(fn) as file:
        expected = json.load(file)

    assert rs.ars_general == expected


def test_routeserver_ars_general_extra_config(db, pdb_data, account_objects):
    rs = account_objects.routeserver

    config_fn = os.path.join(
        os.path.dirname(__file__), "data", "rs", "extra_config.yml"
    )
    with open(config_fn, "rb") as yml_file:
        rs.extra_config = yml_file.read()

    json_fn = os.path.join(
        os.path.dirname(__file__), "data", "rs", "ars_general_extra_config.json"
    )
    with open(json_fn) as file:
        expected = json.load(file)

    assert rs.ars_general == expected


def test_routeserver_ars_clients(db, pdb_data, account_objects):
    rs = account_objects.routeserver

    fn = os.path.join(
        os.path.dirname(__file__), "data", "rs", "ars_clients_default.json"
    )
    with open(fn) as file:
        expected = json.load(file)
    assert rs.ars_clients == expected


def test_routeserver_rsconf(db, pdb_data, account_objects):
    rs = account_objects.routeserver
    # This property creates a config if it doesn't already exist
    rs.rsconf
    assert models.RouteserverConfig.objects.filter(rs=rs).exists()


def test_rsconf(db, pdb_data, account_objects):
    try:
        from yaml import CDumper as Dumper
    except ImportError:
        from yaml import Dumper
    import yaml

    rs = account_objects.routeserver
    rsconf = rs.rsconf
    # Currently printing an Error but not raising an exception
    # it does save the ars_general and ars_clients fields so
    # we test that.
    rsconf.generate()
    assert rsconf.ars_general == yaml.dump(rs.ars_general, Dumper=Dumper)
    assert rsconf.ars_clients == yaml.dump(rs.ars_clients, Dumper=Dumper)


def test_rsconf_outdated_update_rs(db, pdb_data, account_objects):
    rs = account_objects.routeserver
    rsconf = rs.rsconf

    assert rsconf.outdated is False
    # Update rs
    rs.ars_type = "bird2"
    rs.save()
    assert rsconf.outdated is True


def test_rsconf_outdated_update_ixmember(db, pdb_data, account_objects):
    rs = account_objects.routeserver
    rsconf = rs.rsconf
    assert rsconf.outdated is False

    ixmember = rs.ix.member_set.filter(is_rs_peer=True).first()
    ixmember.name = "Changed name"
    ixmember.save()
    assert rsconf.outdated is True
