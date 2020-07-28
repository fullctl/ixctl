from django_grainy.helpers import int_flags

from django_ixctl.models import (
    Organization,
    OrganizationUser,
    APIKey,
)


def sync_api_keys(backend, details, response, uid, user, *args, **kwargs):
    social = kwargs.get("social") or backend.strategy.storage.user.get_social_auth(
        backend.name, uid
    )
    if social:
        api_keys = social.extra_data.get("api_keys", [])

        api_keys = dict([(api_key["key"], api_key["perms"]) for api_key in api_keys])
        print("SYNCING API KEYS", api_keys)

        # delete / update existing keys

        for api_key in user.key_set.all():
            if api_key.key not in api_keys:
                # delete old keys
                api_key.delete()
            else:
                # exiting key, update permissions
                _sync_api_key_permissions(api_key, api_keys.get(api_key.key))

        # create new keys

        for new_key, permissions in api_keys.items():
            api_key, created = APIKey.objects.get_or_create(user=user, key=new_key,)


def sync_organizations(backend, details, response, uid, user, *args, **kwargs):
    social = kwargs.get("social") or backend.strategy.storage.user.get_social_auth(
        backend.name, uid
    )
    if social:
        organizations = social.extra_data.get("organizations", [])
        Organization.sync(organizations, user)
