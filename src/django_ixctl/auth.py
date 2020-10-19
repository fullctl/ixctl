from django.conf import settings

import django_grainy.util
import django_grainy.remote


class Permissions(django_grainy.util.Permissions):
    pass


class RemotePermissions(django_grainy.remote.Permissions):

    """
    When MANAGED_BY_OAUTH is True, permissions are provided
    from the oauth instance.

    We use grainy remote permissions to facilitate this
    """

    def __init__(self, obj):
        super().__init__(obj, **settings.GRAINY_REMOTE)

    def prepare_request(self, params, headers):
        try:
            key = self.obj.key_set.first().key
            print("KEY", key)
            headers.update(Authorization=f"Bearer {key}")
        except AttributeError:
            pass


def permissions(user, refresh=False):
    if hasattr(user, "_ixctl_permissions") and not refresh:
        return user._ixctl_permissions
    if settings.MANAGED_BY_OAUTH:
        perms = RemotePermissions(user)
    else:
        perms = Permissions(user)
    user._ixctl_permissions = perms
    return perms

