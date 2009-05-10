# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.simple import direct_to_template
from ragendja.urlsauto import urlpatterns
from ragendja.auth.urls import urlpatterns as auth_patterns
#from myapp.forms import UserRegistrationForm
from django.contrib import admin

admin.autodiscover()

handler500 = 'ragendja.views.server_error'

urlpatterns = auth_patterns + patterns('',
    ('^admin/(.*)', admin.site.root),
    #(r'^$', 'django.views.generic.simple.direct_to_template',
    #    {'template': 'main.html'}),
    # Override the default registration form
    #url(r'^account/register/$', 'registration.views.register',
    #    kwargs={'form_class': UserCreationForm},
    #    name='registration_register'),
    (r'^$', 'archive.views.index'),
    (r'^archive/',  include('archive.urls')),
    (r'^q/(?P<query>.+)$', 'trend.views.show'),
    (r'^account/', include('registration.urls')),
    (r'^trend/', include('trend.urls')),
    (r'^feed/', include('feed.urls')),
    url(r'^gadget/$',
        direct_to_template,
        {'template': 'gadget.html'},
        name='gadget'),
) + urlpatterns
