from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import django_ixctl.models as models
from django_ixctl.rest import BadRequest

from django_ixctl.rest.serializers.account import Serializers
from django_ixctl.rest.route.account import route
from django_ixctl.rest.decorators import disable_api_key, set_org, grainy_endpoint


@route
class Organization(viewsets.GenericViewSet):

    """
    Manage user's organizations
    """

    serializer_class = Serializers.org
    queryset = models.Organization.objects.all()

    def list(self, request, *args, **kwargs):

        """
        list the organizations that the user belongs
        to or has permissions to
        """


        serializer = Serializers.org(
            instance=models.Organization.accessible(request.user),
            many=True,
            context={"user": request.user},
        )
        return Response(serializer.data)



@route
class User(viewsets.GenericViewSet):

    ref_tag = "user"


    @action(detail=False, methods=["GET"])
    @grainy_endpoint()
    def asns(self, request, org, *args, **kwargs):
        serializer = Serializers.asn(
            verified_asns(request.perms),
            many=True
        )
        return Response(serializer.data)




