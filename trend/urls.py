# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('trend.views',
    (r'^$', 'index'),
    (r'^list/$', 'list'),
)
