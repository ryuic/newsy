# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('feed.views',
    (r'^$', 'index'),
    (r'^generate/$', 'generate'),
    (r'^add/$', 'create'),
    (r'^show/(?P<key>.+)$', 'show'),
    (r'^edit/(?P<key>.+)$', 'edit'),
    (r'^delete/(?P<key>.+)$', 'delete'),
    (r'^crawl/', 'crawl'),
    #(r'^download/(?P<key>.+)/(?P<name>.+)$', 'download_file'),
)
