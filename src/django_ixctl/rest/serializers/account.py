import re

from rest_framework import serializers

from django_ixctl.rest.decorators import serializer_registry
from django_ixctl.rest.serializers import ModelSerializer

import django_ixctl.models as models

Serializers, register = serializer_registry()


@register
class Organization(ModelSerializer):
    selected = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    access_type = serializers.SerializerMethodField()

    class Meta:
        model = models.Organization
        fields = ["slug", "name", "selected", "personal", "access_type"]

    def get_access_type(self, obj):
        user = self.context.get("user")
        if user and not user.org_set.filter(org_id=obj.id).exists():
            return "customer"
        return "member"

    def get_selected(self, obj):
        org = self.context.get("org")
        return obj == org

    def get_name(self, obj):
        if obj.personal:
            return "Personal"
        return obj.name
