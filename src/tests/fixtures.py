import os.path
import pytest
import json
from django.conf import settings
from django.test import Client

# lazy init for translations
_ = lambda s: s


class AccountObjects:
    def __init__(self, handle):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from django_grainy.util import Permissions
        from django_ixctl.models import Organization, OrganizationUser

        self.user = user = get_user_model().objects.create_user(
            username=f"user_{handle}", email=f"{handle}@localhost", password="test",
        )

        self.orgs = Organization.sync(
            [
                {
                    "id": 1,
                    "name": f"ORG{handle}",
                    "slug": handle,
                    "personal": True,
                },
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

        self.org = self.orgs[0]

        # Organization.create(**{
        #             "id": 1,
        #             "name": f"ORG{handle}",
        #             "slug": handle,
        #             "personal": True,
        #         }
        #     )
        self.other_org = Organization.objects.create(name="Other", slug="other", id=3,)

        self.api_client = APIClient()
        self.api_client.login(username=user.username, password="test")

        self.client = Client()
        self.client.login(username=user.username, password="test")

        self.perms = Permissions(user)

    @property
    def ixctl_instance(self):

        from django_ixctl.models import Instance

        if not hasattr(self, "_ixctl_instance"):
            self._ixctl_instance = Instance.objects.create(org=self.org)

        return self._ixctl_instance

    @property
    def pdb_net(self):
        from django_peeringdb.models.concrete import Network

        if not hasattr(self, "_pdb_net"):
            self._pdb_net = Network.objects.get(asn=63311)
        return self._pdb_net

    @property
    def pdb_ix(self):
        from django_peeringdb.models.concrete import InternetExchange

        if not hasattr(self, "_pdb_ix"):
            self._pdb_ix = InternetExchange.objects.get(id=239)
        return self._pdb_ix

    @property
    def pdb_ixlan(self):
        return self.pdb_ix.ixlan_set.first()

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
    def net(self):
        from django_ixctl.models import Network

        if not hasattr(self, "_net"):
            try:
                self._net = Network.objects.get(
                    instance=self.ixctl_instance, pdb_id=self.pdb_net.id
                )
            except Network.DoesNotExist:
                self._net = Network.create_from_pdb(self.ixctl_instance, self.pdb_net)
        return self._net


@pytest.fixture
def pdb_data():
    """
    import initial pdb data
    """
    from django.core.management import call_command

    path = os.path.join(os.path.dirname(__file__), "data", "pdb", "pdb.json")
    print(f"Loading from {path}")
    call_command("loaddata", path)


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
