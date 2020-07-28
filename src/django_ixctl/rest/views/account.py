from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import django_ixctl.models as models

from django_ixctl.rest.serializers.account import Serializers
from django_ixctl.rest.route.account import route
from django_ixctl.rest.decorators import disable_api_key, set_org, grainy_endpoint


@route
class Organization(viewsets.ViewSet):

    serializer_class = Serializers.org
    queryset = models.Organization.objects.all()

    @grainy_endpoint()
    def list(self, request, org, *args, **kwargs):
        serializer = Serializers.org(
            instance=[o.org for o in request.user.org_set.all()],
            many=True,
            context={"user": request.user, "org": org},
        )
        return Response(serializer.data)


    @action(detail=False, methods=["GET"])
    @grainy_endpoint()
    def users(self, request, org, *args, **kwargs):
        serializer = Serializers.orguser(
            org.user_set.all(),
            many=True,
            context={
                "user": request.user,
                "perms": request.perms,
            },
        )
        return Response(serializer.data)

