# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from django.views.generic.list_detail import object_list, object_detail
from feed.models import CategoryCount, Feed, Entry
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response, JSONResponse
from lib import clusters
import logging

#@cache_page(900)
def index(request):
    #categories
    categories = cache.get('categories')
    if not categories:
        categories = CategoryCount.all().fetch(20)
        cache.set('categories', categories, 864000)

    payload = {
        'categories' : categories,
        'recent_entries' : get_entries('recent', expire=900),
        'google_entries' : get_entries('Google', categories),
        'apple_entries' : get_entries('Apple', categories),
        'microsoft_entries' : get_entries('Microsoft', categories),
        'web_entries' : get_entries('Web', categories),
        'gadget_entries' : get_entries('Gadgets', categories),
        'software_entries' : get_entries('Software', categories),
        'other_entries' : get_entries('Other', categories),
    }

    return render_to_response(request, 'archive/index.html',payload)

@cache_page(900)
def list(request, cat=None, blog=None, label=None):
    entry_obj = Entry.all().order('-created_at')

    if cat:
        cat_obj = CategoryCount.all().filter('category =', cat).get()
        if not cat_obj: raise Http404
        entry_obj.filter('cat_ref =', cat_obj)
        label = cat_obj.category
    elif blog:
        feed_obj = get_object_or_404(Feed, blog)
        entry_obj.filter('feed_ref =', feed_obj)
        label = feed_obj.name

    template_ext = 'xml' if request.GET.has_key('output') and request.GET.get('output') == 'rss' else 'html'

    return object_list(request, entry_obj, paginate_by=25,
                       extra_context={'label' : label, 'cat' : cat, 'blog' : blog},
                       template_name='archive/entry_list.%s' % template_ext)

def jsonlist(request, cat):
    markup = "_jsonlist_%s" % cat
    res = cache.get(markup)
    if not res:
        category = CategoryCount.all().filter('category =', cat).get()
        entry_obj = get_entries(cat, category=category)

        entries = []
        for e in entry_obj: entries.append({'title' : e.title, 'url' : e.url})

        res = JSONResponse({'entries' : entries})
        cache.set(markup, res, 1800)
    return res

def show(request, key):
    return object_detail(request, Entry.all(), key, template_name='archive/entry_detail.html')

def get_entries(name, categories=None, category=None, limit=10, expire=86400):
    markup = '%s_entries' % name
    entries = cache.get(markup)

    if not entries:
        try:
            entry_obj = Entry.all().order('-created_at')
            if categories:
                cat = get_cat_key(name, categories)
                entries = entry_obj.filter('cat_ref =', cat)
            elif category:
                entries = entry_obj.filter('cat_ref =', category)
            entries = entry_obj.fetch(limit)
            cache.set(markup, entries, expire)
        except:
            return []

    return entries

def get_cat_key(cat, categories):
    for c in categories:
        if c.category == cat: return c
    raise TypeError, 'Undifined category was required. %s' % cat
    