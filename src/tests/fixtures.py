import os.path

import fullctl.service_bridge.pdbctl as pdbctl
import pytest
from django.test import Client

# lazy init for translations
_ = lambda s: s  # noqa: E731


def reset_auto_fields():
    from django.core.management.color import no_style
    from django.db import connection

    from django_ixctl.models import Organization

    sequence_sql = connection.ops.sequence_reset_sql(no_style(), [Organization])
    with connection.cursor() as cursor:
        for sql in sequence_sql:
            cursor.execute(sql)


class AccountObjects:
    def __init__(self, handle):
        from django.contrib.auth import get_user_model
        from fullctl.django.auth import permissions
        from fullctl.django.models.concrete import OrganizationUser
        from rest_framework.test import APIClient

        from django_ixctl.models import Organization

        reset_auto_fields()

        self.user = user = get_user_model().objects.create_user(
            username=f"user_{handle}",
            email=f"{handle}@localhost",
            password="test",
            first_name=f"user_{handle}",
            last_name="last_name",
        )

        self.other_user = get_user_model().objects.create_user(
            username=f"other_user_{handle}",
            email=f"other_{handle}@localhost",
            password="test",
            first_name=f"other_user_{handle}",
            last_name="last_name",
        )

        self.orgs = Organization.sync(
            [
                {"id": 1, "name": f"ORG{handle}", "slug": handle, "personal": True},
                {
                    "id": 2,
                    "name": f"ORG{handle}-2",
                    "slug": f"{handle}-2",
                    "personal": False,
                },
            ],
            user,
            None,
        )

        # add permissions
        user.grainy_permissions.add_permission(self.orgs[0], "crud")
        user.grainy_permissions.add_permission(f"*.{self.orgs[0].id}", "crud")
        user.grainy_permissions.add_permission(f"config.*.{self.orgs[0].id}", "crud")
        user.grainy_permissions.add_permission(self.orgs[1], "r")
        user.grainy_permissions.add_permission(f"*.{self.orgs[1].id}", "r")
        user.grainy_permissions.add_permission(f"config.*.{self.orgs[1].id}", "r")

        self.org = self.orgs[0]

        OrganizationUser.objects.create(org=self.org, user=self.other_user)

        self.other_org = Organization.objects.create(
            name="Other",
            slug="other",
            id=3,
        )

        self.api_client = APIClient()
        self.api_client.login(username=user.username, password="test")

        self.client = Client()
        self.client.login(username=user.username, password="test")
        self.perms = permissions(user, refresh=True)

    @property
    def ixctl_instance(self):

        from django_ixctl.models import Instance

        if not hasattr(self, "_ixctl_instance"):
            self._ixctl_instance = Instance.objects.create(org=self.org)

        return self._ixctl_instance

    @property
    def pdb_net(self):
        return pdbctl.Network().object(20)

    @property
    def pdb_ix(self):
        return pdbctl.InternetExchange().object(239)

    @property
    def pdb_ixlan(self):
        return pdbctl.InternetExchange().object(239)

    @property
    def ix(self):
        from django_ixctl.models import InternetExchange

        if not hasattr(self, "_ix"):
            try:
                self._ix = InternetExchange.objects.get(
                    instance=self.ixctl_instance, pdb_id=self.pdb_ixlan.id
                )
            except InternetExchange.DoesNotExist:
                self._ix = InternetExchange.create_from_pdb(
                    self.ixctl_instance, self.pdb_ixlan
                )
        return self._ix

    @property
    def routeserver(self):
        from django_ixctl.models import Routeserver

        kwargs = {
            "ix": self.ix,
            "name": "test routeserver",
            "asn": self.pdb_net.asn,
            "router_id": "192.168.0.1",
            "rpki_bgp_origin_validation": False,
            "ars_type": "bird",
            "max_as_path_length": 32,
        }
        if not hasattr(self, "_rs"):
            self._rs = Routeserver.objects.create(**kwargs)
        return self._rs


def make_account_objects(handle="test"):
    return AccountObjects(handle)


@pytest.fixture
def client_anon():
    return Client()


@pytest.fixture
def account_objects():
    return make_account_objects()


@pytest.fixture
def account_objects_b():
    return make_account_objects("test_b")


@pytest.fixture
def pdb_data():
    import fullctl.service_bridge.client as client

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    client.TEST_DATA_PATH = data_dir
