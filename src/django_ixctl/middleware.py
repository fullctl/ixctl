from django.http import Http404
from django_ixctl.models import Organization, OrganizationUser
from django_ixctl.auth import Permissions

from django.conf import settings


class RequestAugmentation:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        kwargs = request.resolver_match.kwargs

        request.perms = Permissions(request.user)

        if not hasattr(request.user, "org_set") and "org_tag" not in kwargs:

            if not settings.ORGANIZATION_PROVIDED_BY_OAUTH:
                request.org = Organization.objects.create(
                    name = f"{request.user.username} personal org",
                    slug = request.user.username,
                    personal = True
                )

                OrganizationUser.objects.create(
                    org = request.org,
                    user = request.user,
                )

                request.orgs = [request.org]
                return
            else:
                request.org = Organization(name="Guest")
                return

        try:
            if "org_tag" in kwargs:
                request.org = Organization.objects.get(slug=kwargs["org_tag"])

            elif request.user.org_set.exists():
                request.org = request.user.org_set.first().org

            if hasattr(request.user, "org_set"):
                request.orgs = request.user.org_set.all()
            else:
                request.orgs = []
        except Organization.DoesNotExist:
            raise Http404

        if not getattr(request, "org", None):
            request.org = Organization(name="Guest")
            return
