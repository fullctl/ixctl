import re
from django.utils.translation import ugettext as _
from django.conf import settings
from rest_framework.schemas.openapi import AutoSchema

class BaseSchema(AutoSchema):

    """
    Augments the openapi schema generation for
    the peeringdb API docs
    """

    # map django internal types to openapi types

    def get_operation_type(self, *args):
        """
        Determine if this is a list retrieval operation
        """

        method = args[1]

        if method == "GET" and "{id}" not in args[0]:
            return "list"
        elif method == "GET":
            return "retrieve"
        elif method == "POST":
            return "create"
        elif method == "PUT":
            return "update"
        elif method == "DELETE":
            return "delete"
        elif method == "PATCH":
            return "patch"

        return method.lower()

    def _get_operation_id(self, path, method):
        """
        We override this so operation ids become "{op} {reftag}"
        """

        serializer, model = self.get_classes(path, method)
        op_type = self.get_operation_type(path, method)

        if model:
            return f"{op_type} {model.HandleRef.tag}"

        return super()._get_operation_id(path, method)

    def get_classes(self, *op_args):
        """
        Try to relate a serializer and model class to the openapi operation

        Returns:

        - tuple(serializers.Serializer, models.Model)
        """

        serializer = self._get_serializer(*op_args)
        model = None
        if hasattr(serializer, "Meta"):
            if hasattr(serializer.Meta, "model"):
                model = serializer.Meta.model
        return (serializer, model)

    def get_operation_type(self, *args):
            """
            Determine if this is a list retrieval operation
            """

            method = args[1]

            if method == "GET" and "{id}" not in args[0]:
                return "list"
            elif method == "GET":
                return "retrieve"
            elif method == "POST":
                return "create"
            elif method == "PUT":
                return "update"
            elif method == "DELETE":
                return "delete"
            elif method == "PATCH":
                return "patch"

            return method.lower()
