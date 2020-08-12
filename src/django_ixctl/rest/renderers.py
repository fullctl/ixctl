import json
from django.db import connection, IntegrityError
from django.utils.encoding import smart_text
from rest_framework import status, renderers
from rest_framework.utils import encoders


class JSONEncoder(encoders.JSONEncoder):
    """
    Custom json encoder that can handle

    - datetime serialization
    - django country field serialization
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        if isinstance(obj, django_countries.fields.Country):
            return str(obj)

        return encoders.JSONEncoder.default(self, obj)


class JSONRenderer(renderers.JSONRenderer):
    """
    Extended JSON Renderer that

    - wraps data in a container
    - makes sure data is always returned as a list
    """

    charset = "utf-8"

    def render(self, data, media_type=None, renderer_context=None):
        status = renderer_context.get("response").status_code

        container = {"data": [], "errors": {}}

        # FIXME: should be a config value to disable/enable profile
        # info in the response data
        if True:
            container["profiling"] = {"queries": len(connection.queries)}

        if status >= 400:
            container["errors"] = data
        else:
            if isinstance(data, dict):
                container["data"].append(data)
            elif isinstance(data, list):
                container["data"].extend(data)
            else:
                raise TypeError(
                    "REST Renderer does not know what to do with data type `{}` at root".format(
                        type(data)
                    )
                )
        data = container
        indent = None
        request = renderer_context.get("request")
        if request:
            if "pretty" in request.GET:
                indent = 2
        return json.dumps(data, cls=JSONEncoder, indent=indent)


class PlainTextRenderer(renderers.BaseRenderer):
    media_type = "text/plain"
    format = "txt"

    def render(self, data, media_type=None, renderer_context=None):
        return smart_text(data, encoding=self.charset)
