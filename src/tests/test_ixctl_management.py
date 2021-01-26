import pytest
from django.conf import settings
from django.core.management import call_command

import django_ixctl.models as models


def test_rsconf_generate(db, pdb_data, account_objects, capsys):
    assert models.RouteserverConfig.objects.count() == 0
    call_command("ixctl_rsconf_generate")
    assert models.RouteserverConfig.objects.count() == 1
    stdout = capsys.readouterr().out.split("\n")

    assert "Regenerating" in stdout[0]
    assert stdout[1] == "Done"


def test_rsconf_generate_outdated(db, pdb_data, account_objects, capsys):
    rs = account_objects.routeserver
    # Make rsconf outdated
    rs.ars_type = "bird2"
    rs.save()
    call_command("ixctl_rsconf_generate")
    assert models.RouteserverConfig.objects.count() == 1


# Need to figure out how to better revert the settings.USE_TZ
def test_peeringdb_sync_connection_error(db):
    from requests.exceptions import ConnectionError

    with pytest.raises(ConnectionError):
        call_command("ixctl_peeringdb_sync", pdburl="http://invalid")
    settings.USE_TZ = True
    assert settings.USE_TZ
