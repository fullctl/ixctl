from django.conf import settings

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework import serializers

import reversion

from django_grainy.decorators import grainy_rest_viewset, grainy_rest_viewset_response

from django_ixctl.rest import HANDLEREF_FIELDS
from django_ixctl.models import Organization, APIKey


from django_ixctl.auth import Permissions, RemotePermissions


class load_object:

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
            return fn(self, request, *args, **kwargs)
        wrapped.__name__ = fn.__name__
        return wrapped


class grainy_endpoint:
    def __init__(
        self, namespace=None, require_auth=True, explicit=True, instance_class=None,
        **kwargs
    ):
        self.namespace = namespace or ["org", "{request.org.permission_id}"]
        self.require_auth = require_auth
        self.explicit = explicit
        self.instance_class = instance_class
        self.kwargs = kwargs

    def __call__(self, fn):
        decorator = self

        if settings.MANAGED_BY_OAUTH:
            permissions_cls = RemotePermissions
        else:
            permissions_cls = Permissions

        @grainy_rest_viewset_response(
            namespace=decorator.namespace,
            namespace_instance=decorator.namespace,
            explicit=decorator.explicit,
            ignore_grant_all=True,
            permissions_cls=permissions_cls,
            **decorator.kwargs,
        )
        def wrapped(self, request, *args, **kwargs):

            request.org = Organization.objects.get(slug=request.nsparam["org_tag"])

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


def serializer_registry():
    class Serializers:
        pass

    def register(cls):
        if not hasattr(cls, "ref_tag"):
            cls.ref_tag = cls.Meta.model.HandleRef.tag
            cls.Meta.fields += ["grainy"] + HANDLEREF_FIELDS
        setattr(Serializers, cls.ref_tag, cls)
        return cls

    return (Serializers, register)


def set_org(fn):
    def wrapped(self, request, pk, *args, **kwargs):
        if pk == "personal":
            org = request.user.personal_org
        else:
            org = Organization.objects.get(slug=pk)
        kwargs["org"] = org
        return fn(self, request, pk, *args, **kwargs)

    wrapped.__name__ = fn.__name__
    return wrapped


def disable_api_key(fn):
    def wrapped(self, request, *args, **kwargs):
        if hasattr(request, "api_key"):
            raise exceptions.AuthenticationFailed(
                "API key authentication not allowed for this operation"
            )
        return fn(self, request, *args, **kwargs)

    wrapped.__name__ = fn.__name__
    return wrapped
