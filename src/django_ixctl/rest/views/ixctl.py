from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django_ixctl.rest import BadRequest

import django_ixctl.models as models
from django_ixctl.rest.route.ixctl import route
from django_ixctl.rest.serializers.ixctl import Serializers
from django_ixctl.rest.decorators import grainy_endpoint as _grainy_endpoint
from django_ixctl.rest.renderers import PlainTextRenderer
from django_ixctl.peeringdb import import_org



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
        "edit_routeserver": Serializers.rs
    }

    queryset = models.InternetExchange.objects.all()
    ref_tag = "ix"

    def get_serializer_class(self):
        if self.action in self.serializer_class_dict:
            return self.serializer_class_dict[self.action]
        return self.serializer_class


    @grainy_endpoint()
    def list(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.ix(
            instance=models.InternetExchange.objects.filter(instance=instance),
            many=True,
        )
        return Response(serializer.data)

    @grainy_endpoint()
    def retrieve(self, request, org, instance, pk, *args, **kwargs):
        serializer = Serializers.ix(
            instance=models.InternetExchange.objects.get(instance=instance, id=pk),
            many=False,
        )
        return Response(serializer.data)

    @grainy_endpoint()
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

    @action(detail=False, methods=["POST"])
    @grainy_endpoint()
    def import_peeringdb(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.impix(
            data=request.data, context={"instance": instance},
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        ix = serializer.save()

        return Response(Serializers.ix(instance=ix).data)

    @action(detail=True, methods=["GET", "POST", "DELETE", "PUT"])
    @grainy_endpoint()
    def members(self, request, org, instance, pk, *args, **kwargs):
        if request.method == "GET":
            return self.list_members(request, org, instance, pk, *args, **kwargs)
        elif request.method == "POST":
            return self.create_member(request, org, instance, pk, *args, **kwargs)
        elif request.method == "PUT":
            return self.update_member(request, org, instance, pk, *args, **kwargs)
        elif request.method == "DELETE":
            return self.destroy_member(request, org, instance, pk, *args, **kwargs)

    def list_members(self, request, org, instance, pk, *args, **kwargs):
        serializer = Serializers.member(
            instance=models.InternetExchangeMember.objects.filter(
                ix_id=pk, ix__instance=instance
            ).order_by("asn"),
            many=True,
        )

        return Response(serializer.data)

    def destroy_member(self, request, org, instance, pk=None, *args, **kwargs):
        ix = models.InternetExchange.objects.get(instance=instance, id=pk)
        member = models.InternetExchangeMember.objects.get(ix=ix, id=request.data["id"])
        member.delete()
        member.id = request.data.get("id")
        return Response(Serializers.member(instance=member).data)

    def create_member(self, request, org, instance, pk=None, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=pk).id
        serializer = Serializers.member(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    def update_member(self, request, org, instance, pk=None, *args, **kwargs):
        member = models.InternetExchangeMember.objects.get(
            ix__instance=instance, ix_id=pk, id=request.data["id"]
        )
        serializer = Serializers.member(
            data=request.data, instance=member, context={"instance": instance}
        )
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    @action(detail=True, methods=["GET", "POST", "PUT", "DELETE"])
    @grainy_endpoint()
    def routeservers(self, request, org, instance, pk=None, *args, **kwargs):
        if request.method == "GET":
            return self.list_routeservers(request, org, instance, pk, *args, **kwargs)
        elif request.method == "POST":
            return self.create_routeserver(request, org, instance, pk, *args, **kwargs)
        elif request.method == "PUT":
            return self.update_routeserver(request, org, instance, pk, *args, **kwargs)
        elif request.method == "DELETE":
            return self.destroy_routeserver(request, org, instance, pk, *args, **kwargs)


    def list_routeservers(self, request, org, instance, pk=None, *args, **kwargs):

        serializer = Serializers.rs(
            instance=models.Routeserver.objects.filter(
                ix_id=pk, ix__instance=instance
            ).order_by("name"),
            many=True,
        )

        return Response(serializer.data)

    def destroy_routeserver(self, request, org, instance, pk=None, *args, **kwargs):
        ix = models.InternetExchange.objects.get(instance=instance, id=pk)
        routeserver = models.Routeserver.objects.get(ix=ix, id=request.data["id"])
        routeserver.delete()
        routeserver.id = request.data.get("id")
        return Response(Serializers.rs(instance=routeserver).data)

    def create_routeserver(self, request, org, instance, pk=None, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=pk).id
        serializer = Serializers.rs(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        return Response(Serializers.rs(instance=routeserver).data)

    def update_routeserver(self, request, org, instance, pk=None, *args, **kwargs):
        routeserver = models.Routeserver.objects.get(
            ix__instance=instance, ix_id=pk, id=request.data["id"]
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

    @grainy_endpoint()
    def retrieve(self, request, org, instance, pk, *args, **kwargs):
        serializer = Serializers.rsconf(
            instance=models.RouteserverConfig.objects.get(
                rs__ix__instance=instance, rs__router_id=pk
            ),
            many=False,
        )
        return Response(serializer.data)

    @action(detail=True, methods=["GET"], renderer_classes=[PlainTextRenderer])
    @grainy_endpoint()
    def plain(self, request, org, instance, pk, *args, **kwargs):
        serializer = Serializers.rsconf(
            instance=models.RouteserverConfig.objects.get(
                rs__ix__instance=instance, rs__router_id=pk
            ),
            many=False,
        )
        return Response(serializer.instance.body)

@route
class User(viewsets.ViewSet):

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
