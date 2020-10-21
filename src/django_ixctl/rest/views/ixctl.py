import re
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from django_ixctl.rest import BadRequest

import django_ixctl.models as models
from django_ixctl.rest.route.ixctl import route

from django_ixctl.rest.serializers.ixctl import Serializers
from django_ixctl.rest.filters import CaseInsensitiveOrderingFilter
from django_ixctl.rest.decorators import grainy_endpoint as _grainy_endpoint, load_object
from django_ixctl.rest.renderers import PlainTextRenderer
from django_ixctl.peeringdb import import_org
from django_ixctl.util import verified_asns

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


class PeeringDBImportSchema(AutoSchema):
    def __init__(self, *args, **kwargs):
        super(AutoSchema, self).__init__(*args, **kwargs)

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation["responses"] = self._get_responses(path, method)
        return operation

    def _get_operation_id(self, path, method):
        return "ix.import_peeringdb"

    def _get_responses(self, path, method):
        self.response_media_types = self.map_renderers(path, method)
        serializer = Serializers.ix()
        response_schema = self._map_serializer(serializer)
        status_code = "200"

        return {
            status_code: {
                "content": {
                    ct: {"schema": response_schema} for ct in self.response_media_types
                },
                "description": "",
            }
        }


@route
class InternetExchange(viewsets.GenericViewSet):
    """
    retrieve:
        Return a internet exchange instance.

    list:
        Return all internet exchanges.

    create:
        Create a new internet exchange.

    import_peeringdb:
        Import an internet exhange from Peeringdb.

    update:
        Update a user.
    """

    serializer_class = Serializers.ix
    serializer_class_dict = {
        "list": Serializers.ix,
        "retrieve": Serializers.ix,
        "create": Serializers.ix,
        "import_peeringdb": Serializers.impix,
        "members": Serializers.member,
        "add_member": Serializers.member,
        "delete_member": Serializers.member,
        "routeservers": Serializers.rs,
        "add_routeserver": Serializers.rs,
        "edit_routeserver": Serializers.rs,
    }

    queryset = models.InternetExchange.objects.all()
    ref_tag = "ix"

    def get_serializer_class(self):
        if self.action in self.serializer_class_dict:
            return self.serializer_class_dict[self.action]
        return self.serializer_class

    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def list(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.ix(
            instance=models.InternetExchange.objects.filter(instance=instance),
            many=True,
        )
        return Response(serializer.data)

    @grainy_endpoint(namespace="ix.{request.org.permission_id}.{pk}")
    def retrieve(self, request, org, instance, pk, *args, **kwargs):
        serializer = Serializers.ix(
            instance=models.InternetExchange.objects.get(instance=instance, id=pk),
            many=False,
        )
        return Response(serializer.data)

    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def create(self, request, org, instance, *args, **kwargs):
        data = request.data
        data["pdb_id"] = None
        serializer = Serializers.ix(data=data)
        if not serializer.is_valid():
            return BadRequest(serializer.errors)
        ix = serializer.save()
        ix.instance = instance
        ix.save()
        return Response(Serializers.ix(instance=ix).data)

    @action(detail=False, methods=["POST"], schema=PeeringDBImportSchema())
    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def import_peeringdb(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.impix(
            data=request.data, context={"instance": instance},
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        ix = serializer.save()

        return Response(Serializers.ix(instance=ix).data)

    @action(detail=True, methods=["GET", "POST"])
    @grainy_endpoint(
        namespace = "member.{request.org.permission_id}.{pk}.?",
        handlers = {
            "*" : { "key": lambda row,idx: row["asn"] }
        }
    )
    def members(self, request, org, instance, pk, *args, **kwargs):
        if request.method == "POST":
            return self._create_member(request, org, instance, pk, *args, **kwargs)
        else:
            return self._list_members(request, org, instance, pk, *args, **kwargs)

    @action(
        detail=True,
        url_path="members/(?P<member_id>[^/.]+)",
        serializer_class=Serializers.member,
        methods=["PUT", "DELETE"],
    )
    @load_object("member", models.InternetExchangeMember, id="member_id")
    @grainy_endpoint(
        namespace = "member.{request.org.permission_id}.{pk}.{member.asn}.?",
    )
    def member(self, request, org, instance, pk, member_id=None, *args, **kwargs):
        if request.method == "PUT":
            return self._update_member(
                request, org, instance, pk, member_id, *args, **kwargs
            )
        elif request.method == "DELETE":
            return self._destroy_member(
                request, org, instance, pk, member_id, *args, **kwargs
            )

    def _list_members(self, request, org, instance, pk, *args, **kwargs):
        ordering_filter = CaseInsensitiveOrderingFilter(
            ["name", "asn", "ipaddr4", "ipaddr6", "speed"]
        )

        queryset = models.InternetExchangeMember.objects.filter(
                ix_id=pk,
                ix__instance=instance
            ).select_related("ix", "ix__instance")

        queryset = ordering_filter.filter_queryset(request, queryset, self)

        serializer = Serializers.member(
            instance=queryset,
            many=True,
        )

        return Response(serializer.data)

    def _destroy_member(self, request, org, instance, pk, member_id, *args, **kwargs):
        ix = models.InternetExchange.objects.get(instance=instance, id=pk)
        member = models.InternetExchangeMember.objects.get(ix=ix, id=member_id)
        member.delete()
        member.id = request.data.get("id")
        return Response(Serializers.member(instance=member).data)

    def _create_member(self, request, org, instance, pk, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=pk).id
        serializer = Serializers.member(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    def _update_member(self, request, org, instance, pk, member_id, *args, **kwargs):
        member = kwargs.get("member")

        serializer = request.grainy_update_serializer(
            Serializers.member,
            member,
            context={"instance": instance}
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    @action(detail=True, methods=["GET", "POST"], serializer_class=Serializers.rs)
    @grainy_endpoint(
        namespace = "rs.{request.org.permission_id}.{pk}.?",
        handlers = {
            "*" : { "key": lambda row,idx: row["asn"] }
        }
    )
    def routeservers(self, request, org, instance, pk=None, *args, **kwargs):
        if request.method == "GET":
            return self._list_routeservers(request, org, instance, pk, *args, **kwargs)
        elif request.method == "POST":
            return self._create_routeserver(request, org, instance, pk, *args, **kwargs)

    @action(
        detail=True,
        url_path="routeservers/(?P<rs_id>[^/.]+)",
        serializer_class=Serializers.rs,
        methods=["PUT", "DELETE"],
    )
    @grainy_endpoint(
        namespace = "rs.{request.org.permission_id}.{pk}.{rs_id}",
    )
    def routeserver(self, request, org, instance, pk, rs_id, *args, **kwargs):
        if request.method == "PUT":
            return self._update_routeserver(
                request, org, instance, pk, rs_id, *args, **kwargs
            )
        elif request.method == "DELETE":
            return self._destroy_routeserver(
                request, org, instance, pk, rs_id, *args, **kwargs
            )

    def _list_routeservers(self, request, org, instance, pk, *args, **kwargs):

        serializer = Serializers.rs(
            instance=models.Routeserver.objects.filter(
                ix_id=pk, ix__instance=instance
            ).order_by("name"),
            many=True,
        )

        return Response(serializer.data)

    def _destroy_routeserver(self, request, org, instance, pk, rs_id, *args, **kwargs):
        ix = models.InternetExchange.objects.get(instance=instance, id=pk)
        routeserver = models.Routeserver.objects.get(ix=ix, id=rs_id)
        routeserver.delete()
        routeserver.id = request.data.get("id")
        return Response(Serializers.rs(instance=routeserver).data)

    def _create_routeserver(self, request, org, instance, pk, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=pk).id
        serializer = Serializers.rs(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        return Response(Serializers.rs(instance=routeserver).data)

    def _update_routeserver(self, request, org, instance, pk, rs_id, *args, **kwargs):
        routeserver = models.Routeserver.objects.get(
            ix__instance=instance, ix_id=pk, id=rs_id
        )
        serializer = Serializers.rs(
            data=request.data, instance=routeserver, context={"instance": instance}
        )
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        return Response(Serializers.rs(instance=routeserver).data)


@route
class RouteserverConfig(viewsets.GenericViewSet):
    serializer_class = Serializers.rsconf
    queryset = models.RouteserverConfig.objects.all()
    lookup_value_regex = "[0-9.]+"
    lookup_url_kwarg = "router_id"

    @grainy_endpoint(
        namespace = "rsconf.{request.org.permission_id}.{pk}",
    )
    def retrieve(self, request, org, instance, pk, *args, **kwargs):
        serializer = Serializers.rsconf(
            instance=models.RouteserverConfig.objects.get(
                rs__ix__instance=instance, rs__router_id=pk
            ),
            many=False,
        )
        return Response(serializer.data)

    @action(detail=True, methods=["GET"], renderer_classes=[PlainTextRenderer])
    @grainy_endpoint(
        namespace = "rsconf.{request.org.permission_id}.{pk}",
    )
    def plain(self, request, org, instance, pk, *args, **kwargs):
        serializer = Serializers.rsconf(
            instance=models.RouteserverConfig.objects.get(
                rs__ix__instance=instance, rs__router_id=pk
            ),
            many=False,
        )
        return Response(serializer.instance.body)


@route
class Network(viewsets.GenericViewSet):
    serializer_class = Serializers.net
    queryset = models.Network.objects.all()

    lookup_url_kwarfs = "asn"


    @grainy_endpoint(
        namespace = "net.{request.org.permission_id}"
    )
    def list(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.net(
            instance.net_set.all(),
            many=True,
        )
        return Response(serializer.data)

    @action(
        detail=False, methods=["GET"], url_path="presence/(?P<asn>[\d]+)"
    )
    @grainy_endpoint(
        namespace = "net.{request.org.permission_id}.{asn}"
    )
    @load_object("net", models.Network, asn="asn", instance="instance")
    def presence(self, request, org, instance, asn, net=None, *args, **kwargs):
        serializer = Serializers.presence(
            net.members,
            many=True,
            context={"perms": request.perms, "user": request.user}
        )
        return Response(serializer.data)

@route
class PermissionRequest(viewsets.GenericViewSet):

    serializer_class = Serializers.permreq
    queryset = models.PermissionRequest.objects.all()

    @grainy_endpoint()
    def list(self, request, org, *args, **kwargs):
        serializer = Serializers.permreq(
            org.permreq_set.all(),
            many=True,
            context={"user": request.user, "perms": request.perms,},
        )
        return Response(serializer.data)


    """
    @grainy_endpoint(namespace="?.?")
    def create(self, request, org, instance, *args, **kwargs):
        data = request.data
        data["user"] = request.user.id
        data["org"] = org.id
        serializer = Serializers.permreq(data=data)

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        permreq = serializer.save()
        return Response(serializer.data)
    """


@route
class User(viewsets.GenericViewSet):

    """
    List users at the organization
    """

    serializer_class = Serializers.orguser
    queryset = models.OrganizationUser.objects.all()
    ref_tag = "user"

    @grainy_endpoint()
    def list(self, request, org, *args, **kwargs):
        serializer = Serializers.orguser(
            org.user_set.all(),
            many=True,
            context={"user": request.user, "perms": request.perms,},
        )
        return Response(serializer.data)




