from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions

from django_ixctl.models import APIKey
from django_ixctl.auth import Permissions


class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        key = request.GET.get("key")

        if not key:
            auth = request.headers.get("Authorization")
            if auth:
                auth = auth.split(" ")
                if auth[0] == "token":
                    key = auth[1]

        try:
            if key:
                api_key = APIKey.objects.get(key=key)
                request.api_key = api_key
                perms = Permissions(key=api_key)
                return (api_key.user, None)
            else:
                return None
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid api key")
