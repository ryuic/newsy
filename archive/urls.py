# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('archive.views',
    (r'^$', 'index'),
    (r'^list/$', 'list'),
    (r'^c/(?P<cat>[^\/]+)/$', 'list'),
    (r'^b/(?P<blog>[^\/]+)/$', 'list'),
    (r'^c/(?P<cat>[^\/]+)/json/$', 'jsonlist'),
    (r'^e/(?P<key>.+)$', 'show'),
    (r'^tool/$', 'list'),
)
