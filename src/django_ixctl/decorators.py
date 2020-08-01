import reversion
import django.http
import rest_framework
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class require_auth:
    def __call__(self, fn):
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:

                # return redirect(
                #     reverse("social:begin", args=("twentyc",))
                #     + f"?next={request.get_full_path()}"
                # )
                return redirect(reverse("login") + f"?next={request.get_full_path()}")

            return fn(request, *args, **kwargs)

        wrapped.__name__ = fn.__name__
        return wrapped


class load_instance:
    def __init__(self, model, public=False):
        self.model = model
        self.public = public

    def __call__(self, fn):
        model = self.model
        public = self.public

        def wrapped(request, *args, **kwargs):

            org = request.org

            if not public and not request.perms.check(org, "r"):
                raise django.http.Http404()

            try:
                instance, _ = model.objects.get_or_create(org=org)
            except model.DoesNotExist:
                raise django.http.Http404()

            request.app_id = instance.app_id

            return fn(request, instance, *args, **kwargs)

        wrapped.__name__ = fn.__name__
        wrapped.public = public

        return wrapped
