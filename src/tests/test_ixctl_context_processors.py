from django.http import HttpRequest
from fullctl.django import context_processors

# Settings fixture allows for safe manipulations of settings inside test
def test_account_service(db, pdb_data, account_objects, settings):

    request = HttpRequest()
    request.org = account_objects.org

    expected = {
        "urls": {
            "create_org": "localhost/account/org/create/",
            "manage_org": "localhost/account/?org=test",
        }
    }

    settings.MANAGED_BY_OAUTH = True
    context = context_processors.account_service(request)
    print(context["account_service"])

    assert context["oauth_manages_org"] == True
    assert context["account_service"] == expected

    settings.MANAGED_BY_OAUTH = False
    context = context_processors.account_service(request)
    assert context == {}


def test_permissions_crud(db, pdb_data, account_objects, settings):
    request = HttpRequest()
    request.org = account_objects.orgs[0]
    request.perms = account_objects.perms

    full_perms = {
        "create_org_management": True,
        "read_org_management": True,
        "update_org_management": True,
        "delete_org_management": True,
        "create_org_ixctl": True,
        "read_org_ixctl": True,
        "update_org_ixctl": True,
        "delete_org_ixctl": True,
    }

    context = context_processors.permissions(request)
    assert context["permissions"] == full_perms


def test_permissions_readonly(db, pdb_data, account_objects, settings):
    request = HttpRequest()
    request.org = account_objects.orgs[1]
    request.perms = account_objects.perms

    readonly_perms = {
        "create_org_management": False,
        "read_org_management": True,
        "update_org_management": False,
        "delete_org_management": False,
        "create_org_ixctl": False,
        "read_org_ixctl": True,
        "update_org_ixctl": False,
        "delete_org_ixctl": False,
    }

    context = context_processors.permissions(request)
    assert context["permissions"] == readonly_perms


def test_permissions_instance_crud(db, pdb_data, account_objects, settings):
    request = HttpRequest()
    request.org = account_objects.orgs[0]
    request.perms = account_objects.perms
    request.app_id = account_objects.ixctl_instance.app_id

    full_perms = {
        "create_org_management": True,
        "read_org_management": True,
        "update_org_management": True,
        "delete_org_management": True,
        "create_org_ixctl": True,
        "read_org_ixctl": True,
        "update_org_ixctl": True,
        "delete_org_ixctl": True,
        "create_instance": True,
        "read_instance": True,
        "update_instance": True,
        "delete_instance": True,
    }

    context = context_processors.permissions(request)
    assert context["permissions"] == full_perms


def test_permissions_instance_readonly(db, pdb_data, account_objects, settings):
    request = HttpRequest()
    request.org = account_objects.orgs[1]
    request.perms = account_objects.perms
    request.app_id = account_objects.ixctl_instance.app_id

    full_perms = {
        "create_org_management": False,
        "read_org_management": True,
        "update_org_management": False,
        "delete_org_management": False,
        "create_org_ixctl": False,
        "read_org_ixctl": True,
        "update_org_ixctl": False,
        "delete_org_ixctl": False,
        "create_instance": False,
        "read_instance": True,
        "update_instance": False,
        "delete_instance": False,
    }

    context = context_processors.permissions(request)
    assert context["permissions"] == full_perms
