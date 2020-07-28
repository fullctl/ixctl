from django.http import Http404, HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect

import django_ixctl.forms
import django_ixctl.exporters.ixf

from django_ixctl.models import (
    Instance,
    InternetExchange,
    Organization,
)

from django_ixctl.decorators import (
    load_instance,
    require_auth,
)

# Create your views here.


def make_env(request, **kwargs):
    r = {"env": settings.RELEASE_ENV, "version": settings.PACKAGE_VERSION}
    r.update(**kwargs)
    return r


@require_auth()
@load_instance(Instance)
def view_instance(request, instance, **kwargs):
    env = make_env(request, instance=instance, org=instance.org)
    env["forms"] = {"import_ix": django_ixctl.forms.ImportIXForm()}

    return render(request, "ixctl/index.html", env)

@require_auth()
def org_redirect(request):
    return redirect(f"/{request.org.slug}/")


@load_instance(Instance, public=True)
def export_ixf(request, org, urlkey, **kwargs):
    try:
        exchange = InternetExchange.objects.get(urlkey=urlkey)
    except InternetExchange.DoesNotExist:
        raise Http404

    if "pretty" in request.GET:
        pretty = True
    else:
        pretty = False

    rv = django_ixctl.exporters.ixf.export(exchange, pretty=pretty)
    return HttpResponse(rv, content_type="application/json")
