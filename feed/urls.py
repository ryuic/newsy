# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('feed.views',
    (r'^$', 'index'),
    (r'^add/$', 'create'),
    (r'^show/(?P<key>.+)$', 'show'),
    (r'^edit/(?P<key>.+)$', 'edit'),
    (r'^delete/(?P<key>.+)$', 'delete'),
    (r'^crawl/', 'crawl'),
    (r'^entry/(?P<key>.+)?$', 'entry_list'),
    (r'^entry_show/(?P<key>.+)$', 'entry_show'),
    (r'^entry_edit/(?P<key>.+)$', 'entry_edit'),
    (r'^entry_delete/(?P<key>.+)$', 'entry_delete'),
    (r'^entry_train/(?P<key>.+)$', 'train'),
    (r'^entry_untrain/(?P<key>.+)$', 'untrain'),
    (r'^entry_guess/(?P<key>.+)$', 'guess'),
    (r'^refleshclassifier/$', 'refleshclassifier'),
)
