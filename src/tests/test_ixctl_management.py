import pytest
from django.conf import settings
from django.core.management import call_command

import django_ixctl.models as models


@pytest.mark.skip
def test_rsconf_generate(db, pdb_data, account_objects, capsys):
    rs = account_objects.routeserver
    assert list(models.Routeserver.objects.all()) == [rs]
    assert models.RouteserverConfig.objects.count() == 0
    call_command("ixctl_rsconf_generate")
    assert models.RouteserverConfig.objects.count() == 1
    stdout = capsys.readouterr().out.split("\n")

    assert "Regenerating" in stdout[0]
    assert stdout[1] == "Done"


@pytest.mark.skip
def test_rsconf_generate_outdated(db, pdb_data, account_objects, capsys):
    rs = account_objects.routeserver
    # Make rsconf outdated
    rs.ars_type = "bird2"
    rs.save()
    call_command("ixctl_rsconf_generate")
    assert models.RouteserverConfig.objects.count() == 1

