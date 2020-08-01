import re

from rest_framework import serializers

from django_grainy.util import Permissions

from django_ixctl.rest.decorators import serializer_registry

import django_ixctl.models as models

Serializers, register = serializer_registry()


@register
class Organization(serializers.ModelSerializer):
    selected = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.Organization
        fields = ["slug", "name", "selected", "personal"]

    def get_selected(self, obj):
        org = self.context.get("org")
        return obj == org

    def get_name(self, obj):
        if obj.personal:
            return "Personal"
        return obj.name


@register
class OrganizationUser(serializers.ModelSerializer):
    ref_tag = "orguser"

    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    you = serializers.SerializerMethodField()

    class Meta:
        model = models.OrganizationUser
        fields = ["id", "name", "email", "you"]

    def get_name(self, obj):
        return "{} {}".format(obj.user.first_name, obj.user.last_name)

    def get_email(self, obj):
        return obj.user.email

    def get_you(self, obj):
        return obj.user == self.context.get("user")
