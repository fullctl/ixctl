import datetime
import json
import django_countries

from django.db import connection, IntegrityError
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


from rest_framework import status, renderers

HANDLEREF_FIELDS = ["id", "status", "created", "updated"]


class BadRequest(Response):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data, status=400, *args, **kwargs)


def exception_handler(exc, context):
    """
    Custom exception handler for REST responses

    Currently used to properly turn django ObjectDoesNotExist
    errors into 404 api responses.
    """

    # call default handler first

    response = Response({})
    if isinstance(exc, ObjectDoesNotExist):
        response.data = {"errors": {"non_field_errors": "{}".format(exc)}}
        response.status_code = 404
    elif isinstance(exc, IntegrityError):
        response.data = {"non_field_errors": "{}".format(exc)}
        response.status_code = 400
    elif isinstance(exc, Http404):
        if getattr(context.get("request"), "destroyed", False):
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        else:
            response.status_code = 404
    else:
        response = drf_exception_handler(exc, context)

    return response


"""
class ScopedUserRateThrottle(UserRateThrottle):
    scope = None
    def allow_request(self, request, view):
        scopes = getattr(view, "throttle_scopes", {})
        scope = scopes.get(request.method.lower())

        if isinstance(scope, list) and self.scope in scope:
            return super(ScopedUserRateThrottle, self).allow_request(request, view)
        return True

class EmailThrottle(ScopedUserRateThrottle):
    #API throttling for api endpoints that send emails
    scope = "email"
"""
