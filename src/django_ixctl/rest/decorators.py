from django.conf import settings

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework import serializers

import reversion

from django_grainy.decorators import grainy_rest_viewset, grainy_rest_viewset_response

from fullctl.django.rest.core import HANDLEREF_FIELDS
from fullctl.django.models import Organization, APIKey
import django_ixctl.models as models

from fullctl.django.auth import Permissions, RemotePermissions

class load_object:

    """
    Will load an object and pass it to the view handler
    for `model` Model as argument `argname`
    **Arguments**
    - argname (`str`): will be passed as this keyword argument
    - model (`Model`): django model class
    **Keyword Arguments**
    Any keyword argument will be passed as a filter to the
    `get` query
    """

    def __init__(self, argname, model, **filters):
        self.argname = argname
        self.model = model
        self.filters = filters

    def __call__(self, fn):

        decorator = self

        def wrapped(self, request, *args, **kwargs):
            filters = {}
            for field, key in decorator.filters.items():
                filters[field] = kwargs.get(key)

            try:
                kwargs[decorator.argname] = decorator.model.objects.get(**filters)
            except decorator.model.DoesNotExist:
                return Response(status=404)

            print(kwargs)
            return fn(self, request, *args, **kwargs)

        wrapped.__name__ = fn.__name__
        return wrapped


class _grainy_endpoint:
    def __init__(
        self,
        namespace=None,
        require_auth=True,
        explicit=True,
        instance_class=None,
        **kwargs
    ):
        self.namespace = namespace or ["org", "{request.org.permission_id}"]
        self.require_auth = require_auth
        self.explicit = explicit
        self.instance_class = instance_class
        self.kwargs = kwargs

    def __call__(self, fn):
        decorator = self

        if getattr(settings, "USE_LOCAL_PERMISSIONS", False):
            permissions_cls = Permissions
        else:
            permissions_cls = RemotePermissions

        @grainy_rest_viewset_response(
            namespace=decorator.namespace,
            namespace_instance=decorator.namespace,
            explicit=decorator.explicit,
            ignore_grant_all=True,
            permissions_cls=permissions_cls,
            **decorator.kwargs,
        )
        def wrapped(self, request, *args, **kwargs):
            request.org = models.Organization.objects.get(slug=request.nsparam["org_tag"])

            if decorator.require_auth and not request.user.is_authenticated:
                return Response(status=401)

            if decorator.instance_class:
                instance, _ = decorator.instance_class.objects.get_or_create(
                    org=request.org
                )
                kwargs.update(instance=instance)

            with reversion.create_revision():
                reversion.set_user(request.user)
                return fn(self, request, org=request.org, *args, **kwargs)

        wrapped.__name__ = fn.__name__

        return wrapped

class grainy_endpoint(_grainy_endpoint):
    def __init__(self, *args, **kwargs):
        super().__init__(
            instance_class=models.Instance,
            explicit=kwargs.pop("explicit", False),
            *args,
            **kwargs
        )
        if "namespace" not in kwargs:
            self.namespace += ["ixctl"]
