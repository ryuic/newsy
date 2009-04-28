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
from datetime import datetime
from lib import feedparser
import logging, re, md5

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

def entry_list(request, key=None):
    payload = {'feed' : None}
    entries = Entry.all()
    if key:
        feed = get_object_or_404(Feed, key)
        entries.filter('feed_ref =', feed)
        payload['feed'] = feed
    entries.order('-created_at')

    return object_list(request, entries, paginate_by=10, extra_context=payload)

def entry_show(request, key):
    return object_detail(request, Entry.all(), key)

def entry_edit(request, key):
    return update_object(request, object_id=key, form_class=EntryForm)

def entry_delete(request, key):
    return delete_object(request, Entry, object_id=key,
        post_delete_redirect=reverse('feed.views.entry_list'))

def crawl(request):
    now = datetime.now()
    feeds = Feed.all() \
        .fetch(1)
    #    .filter('execute_hour =', now.hour) \
    #    .filter('execute_minute =', now.minute) \
    #    .fetch(100)

    apcount = {}
    wordcounts = {}

    for feed in feeds:
        try:
            logging.info("Start Crawl >>> %s, [%d:%d]" % (feed.url, now.hour, now.minute, now.second))

            d = feedparser.parse(feed.url)
            wc = {}
            for e in d.entries:
                entry, wc = getwordcounts(feed)
                wordcounts[title] = wc

                #apcountの集計
                for word, count in wc.items():
                    apcount.setdefault(word, 0)
                    if count > 1: apcount[word] += 1

            logging.info("End Crawl >>> %s, [%d:%d]" % (feed.url, now.hour, now.minute, now.second))
        except:
            logging.info('Failed to parse feed %s' % feed.url)
            pass

    wordlist = []
    for w, bc in apcount.items():
        frac = float(bc) / len(feeds)
        if frac > 0.1 and frac < 0.5: wordlist.append(w)

    results = []
    for entry, wc in wordcounts.items():
        result = {'blog' : feed.name, 'count' : []}

        for word in wordlist:
            if word in wc: count = wc[word]
            else: count = 0

            #Datastore
            w = Word.all().filter('word =', word).get()
            if not w:
                w = Word({word : word, apcount : count})
                w.save()
            wl = WordList({entry_ref : e, word_ref : w})
            wl.save()

            result['count'].append(count)
        results.append(result)

    return render_to_response(request, 'feed/crawl.html', 
        {'feeds' : feeds, 'results' : results, 'wordlist' : wordlist})

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
        except EntryDuplicateError:
            pass
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

def getwordcounts(e):
    url_hash = md5.new(e.link).hexdigest()
    entry = Entry.all().filter('url_hash =', url_hash).get()
    if entry:
        raise EntryDuplicateError, '%s has been already add.' % e.link

    if 'summary' in e: summary = e.summary
    else: summary = e.description

    words = getwords(e.title + ' ' + e.summary)
    for word in words:
        wc.setdefault(word, 0)
        wc[word] += 1

    entry = Entry(
        feed_ref = feed.key(),
        title = e.title,
        url = e.link,
        description = summary,
        url_hash = url_hash
    )
    entry.save()
    return e, wc

def getwords(html):
    txt = re.compile(r'<[^>]+>').sub('', html)
    words = re.compile(r'[^A-Z^a-z]+').split(txt)
    return [word.lower() for word in words if word != '']

