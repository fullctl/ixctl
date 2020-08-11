from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf import settings


import django_ixctl.views as views
import django_ixctl.autocomplete.views

from rest_framework.schemas import get_schema_view

urlpatterns = [
    path(
        "api/<str:org_tag>/account/",
        include(
            ("django_ixctl.rest.urls.account", "ixctl_account_api"),
            namespace="ixctl_account_api",
        ),
    ),
    path(
        "api/<str:org_tag>/",
        include(("django_ixctl.rest.urls.ixctl", "ixctl_api"), namespace="ixctl_api"),
    ),
    path(
        "autocomplete/pdb/ix",
        django_ixctl.autocomplete.views.peeringdb_ix.as_view(),
        name="pdb ix autocomplete",
    ),
    path(
        "autocomplete/pdb/org",
        django_ixctl.autocomplete.views.peeringdb_org.as_view(),
        name="pdb org autocomplete",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="ixctl/auth/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login"), name="logout"),
    path("<str:org_tag>/export/ixf/<slug:urlkey>", views.export_ixf, name="ixf export"),
    path("<str:org_tag>/", views.view_instance, name="ixctl-home"),
    path("", views.org_redirect),
    path('openapi', 
        get_schema_view(
            title="IXCTL",
            description="API for ixctl",
            version=settings.PACKAGE_VERSION
        ), name='openapi-schema'),
    path("apidocs/swagger",
        TemplateView.as_view(
            template_name='ixctl/apidocs/swagger.html',
            extra_context={'schema_url':'openapi-schema'}
        ), name='swagger'),
    path("apidocs/redoc",
        TemplateView.as_view(
            template_name='ixctl/apidocs/redoc.html',
            extra_context={'schema_url':'openapi-schema'}
        ), name='redoc'),
]
