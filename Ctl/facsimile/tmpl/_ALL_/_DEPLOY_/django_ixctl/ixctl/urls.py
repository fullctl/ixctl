
from django.conf.urls import patterns, include, url
from django.contrib import admin

#from rest_framework import routers
#from django_ixctl import views

admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

#    (r'^grappelli/', include('grappelli.urls')),
#    (r'^admin/',  include(admin.site.urls)),
)

