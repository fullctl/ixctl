
from django.urls import path,include

import django_ixctl.views as views
import django_ixctl.autocomplete.views

urlpatterns = [
    path(
        'api/<str:org_tag>/account/',
        include(("django_ixctl.rest.urls.account", "ixctl_account_api"), namespace="ixctl_account_api"),
    ),
    path(
        'api/<str:org_tag>/',
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
    path("export/ixf/<slug:urlkey>", views.export_ixf, name="ixf export"),

    path('<str:org_tag>/', views.view_instance, name="ixctl-home"),
    path("", views.org_redirect),
]
