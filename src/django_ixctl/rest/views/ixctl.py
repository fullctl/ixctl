from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django_ixctl.rest import BadRequest

import django_ixctl.models as models
from django_ixctl.rest.route.ixctl import route
from django_ixctl.rest.serializers.ixctl import Serializers
from django_ixctl.rest.decorators import grainy_endpoint as _grainy_endpoint
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
class InternetExchange(viewsets.ViewSet):
    serializer_class = Serializers.ix
    queryset = models.InternetExchange.objects.all()
    ref_tag = "ix"

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

    @action(detail=True, methods=["GET"])
    @grainy_endpoint()
    def members(self, request, org, instance, pk=None, *args, **kwargs):

        serializer = Serializers.member(
            instance=models.InternetExchangeMember.objects.filter(
                ix_id=pk, ix__instance=instance
            ).order_by("asn"),
            many=True,
        )

        return Response(serializer.data)

    @action(detail=True, methods=["DELETE"])
    @grainy_endpoint()
    def delete_member(self, request, org, instance, pk=None, *args, **kwargs):
        ix = models.InternetExchange.objects.get(instance=instance, id=pk)
        member = models.InternetExchangeMember.objects.get(ix=ix, id=request.data["id"])
        member.delete()
        member.id = request.data.get("id")
        return Response(Serializers.member(instance=member).data)

    @action(detail=True, methods=["POST"])
    @grainy_endpoint()
    def add_member(self, request, org, instance, pk=None, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=pk).id
        serializer = Serializers.member(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    @action(detail=True, methods=["PUT"])
    @grainy_endpoint()
    def edit_member(self, request, org, instance, pk=None, *args, **kwargs):
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
