# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from google.appengine.ext import db
from feed.forms import *
from feed.models import *
from ragendja.auth.decorators import staff_only
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response

#@staff_only
def index(request):
    return object_list(request, Feed.all().order('-created_at'), paginate_by=10)

def show(request, key):
    return object_detail(request, Feed.all(), key)

def create(request):
    return create_object(request, form_class=FeedForm,
        post_save_redirect=reverse('feed.views.show',
                                   kwargs=dict(key='%(key)s')))

def edit(request, key):
    return update_object(request, object_id=key, form_class=FeedForm)

def delete(request, key):
    return delete_object(request, Feed, object_id=key,
        post_delete_redirect=reverse('feed.views.index'))


def crawl(request):
    
    return render_to_response(request, 'trend/generate.html', {'results' : results})

def generate(request):
    apcount = {}
    wordcounts = {}
    feedlist = [
      'http://feeds.nytimes.com/nyt/rss/Technology',
      'http://feedproxy.google.com/TechCrunch',
      'http://feeds.feedburner.com/readwriteweb'
    ]

    for feedurl in feedlist:
        try:
            title, wc = getwordcounts(feedurl)
            wordcounts[title] = wc
            for word, count in wc.items():
                apcount.setdefault(word, 0)
                if count > 1:
                    apcount[word] += 1
        except:
            pass
            #print 'Failed to parse feed %s' % feedurl

    wordlist = []
    for w, bc in apcount.items():
        frac = float(bc) / len(feedlist)
        if frac > 0.1 and frac < 0.5: wordlist.append(w)

    results = []
    for blog, wc in wordcounts.items():
        result = {'blog' : blog, 'count' : []}

        for word in wordlist:
            if word in wc: count = wc[word]
            else: count = 0
            
            logging.info("count >>> %d" % count)
            
            result['count'].append(count)
        results.append(result)

    return render_to_response(request, 'trend/generate.html', {'results' : results})

def getwordcounts(url):
    d = feedparser.parse(url)
    wc = {}
    for e in d.entries:
        if 'summary' in e: summary = e.summary
        else: summary = e.description

        words = getwords(e.title + ' ' + e.summary)
        for word in words:
            wc.setdefault(word, 0)
            wc[word] += 1
    return d.feed.title, wc

def getwords(html):
    txt = re.compile(r'<[^>]+>').sub('', html)
    words = re.compile(r'[^A-Z^a-z]+').split(txt)
    return [word.lower() for word in words if word != '']

