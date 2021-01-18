from django.urls import path, include
from django_ixctl.rest.views.ixctl import InternetExchange, Members, Routeserver
import django_ixctl.rest.route.ixctl

ix_list = InternetExchange.as_view({
    'get': 'list',
    'post': 'create'
})

ix_detail = InternetExchange.as_view({
    'get': 'retrieve',
})

ix_import_peeringdb = InternetExchange.as_view({
    'post': 'import_peeringdb',
})

member_list = Members.as_view({
    'get': 'list',
    'post': 'create'
})

member_detail = Members.as_view({
    'put': 'update',
    'delete': 'destroy',
})

routeserver_list = Routeserver.as_view({
    'get': 'list',
    'post': 'create',
})

routeserver_detail = Routeserver.as_view({
    'put': 'update',
    'delete': 'destroy',
})

urlpatterns = [
    path('ix/<str:org_tag>/', ix_list, name='ix-list'),
    path('ix/<str:org_tag>/import_peeringdb', ix_import_peeringdb, name='ix-import-peeringdb'),
    path('ix/<str:org_tag>/<str:ix_tag>/', ix_detail, name='ix-detail'),
    path('member/<str:org_tag>/<str:ix_tag>/', member_list, name='member-list'),
    path('member/<str:org_tag>/<str:ix_tag>/<int:member_id>', member_detail, name='member-detail'),
    path('routeserver/<str:org_tag>/<str:ix_tag>/', routeserver_list, name='routeserver-list'),
    path('routeserver/<str:org_tag>/<str:ix_tag>/<int:rs_id>', routeserver_detail, name='routeserver-detail'),
    path("<str:org_tag>/", include(django_ixctl.rest.route.ixctl.router.urls)),
]

