# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('archive.views',
    (r'^$', 'index'),
    (r'^c/(?P<cat>[^\/]+)/$', 'list'),
    (r'^b/(?P<blog>[^\/]+)/$', 'list'),
    (r'^e/(?P<key>.+)$', 'show'),
)
