# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from feed.models import CategoryCount, Feed, Entry
from ragendja.auth.decorators import staff_only
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response, JSONResponse
from lib import clusters
import logging

def index(request):
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

def list(request, cat=None, blog=None, label=''):
    entry_obj = Entry.all().order('-created_at')

    if cat:
        cat_obj = CategoryCount.all().filter('category =', cat).get()
        if not cat_obj: raise Http404
        entry_obj.filter('cat_ref =', cat_obj)
        label = cat_obj.category

    if blog:
        feed_obj = get_object_or_404(Feed, blog)
        entry_obj.filter('feed_ref =', feed_obj)
        label = feed_obj.name

    return object_list(request, entry_obj, paginate_by=25,
                       extra_context={'label' : label, 'cat' : cat, 'blog' : blog},
                       template_name='archive/entry_list.html')

def show(request, key):
    entry = get_object_or_404(Entry, key)

    wordcounts = []
    wordlist = []
    entries = Entry.all().filter('cat_ref =', entry.cat_ref).order('-created_at').fetch(10)

    for e in entries:
        wc = clusters.get_words(e)
        wordcounts.append(wc)
        for w in wc.keys():
            if w not in wordlist: wordlist.append(w)

    words = [[] for i in range(len(wordcounts))]

    i = 0
    for wc in wordcounts:
        for word in wordlist:
            if word in wc: c = wc[word]
            else: c = 0
            words[i].append(c)
        i += 1

    kcluster = clusters.kcluster(words)

    logging.debug(kcluster)

    return render_to_response(request, 'archive/entry_detail.html',
                              {'entry' : entry, 'kcluster' : kcluster, 'words' : words})

def get_entries(name, categories=None, limit=10, expire=86400):
    markup = '%s_entries' % name
    entries = cache.get(markup)

    if not entries:
        try:
            entry_obj = Entry.all().order('-created_at')
            if categories:
                cat = get_cat_key(name, categories)
                entries = entry_obj.filter('cat_ref =', cat)
            entries = entry_obj.fetch(limit)
            cache.set(markup, entries, expire)
        except:
            return []

    return entries

def get_cat_key(cat, categories):
    for c in categories:
        if c.category == cat: return c
    raise TypeError, 'Undifined category was required. %s' % cat
    