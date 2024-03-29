from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from fullctl.django.decorators import load_instance, require_auth

import django_ixctl.exporters.ixf
from django_ixctl.context_processors import check_trial_available
from django_ixctl.models import InternetExchange

# Create your views here.


def make_env(request, **kwargs):
    r = {"env": settings.RELEASE_ENV, "version": settings.PACKAGE_VERSION}
    r.update(**kwargs)
    return r


@require_auth()
@load_instance()
def view_instance(request, instance, **kwargs):
    env = make_env(request, instance=instance, org=instance.org)

    env["select_ix"] = InternetExchange.get_default_exchange_for_org(instance.org)
    if env["select_ix"]:
        env.update(check_trial_available(request.org.slug, env["select_ix"].slug))

    return render(request, "theme-select.html", env)


@require_auth()
@load_instance()
def view_instance_load_ix(request, instance, ix_tag, **kwargs):
    try:
        ix = InternetExchange.objects.get(instance=instance, slug=ix_tag)
    except InternetExchange.DoesNotExist:
        raise Http404

    env = make_env(request, instance=instance, org=instance.org)
    env["select_ix"] = ix
    env.update(check_trial_available(request.org.slug, ix.slug))

    return render(request, "theme-select.html", env)


@require_auth()
def org_redirect(request):
    return redirect(f"/{request.org.slug}/")


@load_instance(public=True)
def export_ixf(request, instance, ix_tag, **kwargs):
    try:
        ix = InternetExchange.objects.get(instance=instance, slug=ix_tag)
    except InternetExchange.DoesNotExist:
        raise Http404

    # Handle private
    if ix.ixf_export_privacy == "private":
        if request.GET.get("secret") != ix.urlkey:
            raise Http404

    if "pretty" in request.GET:
        pretty = True
    else:
        pretty = False

    rv = django_ixctl.exporters.ixf.export(ix, pretty=pretty)
    return HttpResponse(rv, content_type="application/json")
