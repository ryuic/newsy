# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from feed.forms import *
from feed.models import *
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response, JSONResponse
from settings import DEBUG
from datetime import datetime
from lib import feedparser, docclass, clusters
import logging, hashlib


def index(request):
    #return object_list(request, Feed.all().order('-created_at'), paginate_by=30,
    #                   extra_context={'timetable' : timetable})
    feeds = Feed.all().order('-created_at').fetch(50)

    tmp = {}
    for f in feeds:
        for eh in f.execute_hour:
            if eh not in tmp: tmp.setdefault(eh, [])
            tmp[eh].append({
                'hour' : eh,
                'minute' : f.execute_minute,
                'feed' : f.name
            })

    timetable = []
    for i in range(24):
        if i in tmp: timetable.append(tmp[i])

    return render_to_response(request, 'feed/feed_list.html',
                              {'feeds' : feeds, 'timetable' : timetable})

def show(request, key):
    feed = get_object_or_404(Feed, key)
    entries = Entry.all().filter('feed_ref =', feed).order('-created_at')
    return object_detail(request, Feed.all(), key, extra_context={'entries' : entries})

def create(request):
    return create_object(request, form_class=FeedForm,
        post_save_redirect=reverse('feed.views.show',
                                   kwargs=dict(key='%(key)s')))

def edit(request, key):
    return update_object(request, object_id=key, form_class=FeedForm)

def delete(request, key):
    return delete_object(request, Feed, object_id=key,
        post_delete_redirect=reverse('feed.views.index'))

def entry_list(request, key=None, show=None):
    payload = {'key': key}
    entries = Entry.all()
    if key:
        feed = get_object_or_404(Feed, key)
        payload['feed'] = feed
        entries.filter('feed_ref =', feed)
    if show:
        entries.filter('cat_ref =', None)
    entries.order('-created_at')

    return object_list(request, entries, paginate_by=25, extra_context=payload)

def entry_show(request, key):
    entry = get_object_or_404(Entry, key)

    #clustering
    wordcounts = []
    wordlist = []

    entries = Entry.all().filter('cat_ref =', entry.cat_ref).order('-created_at').fetch(20)

    for e in entries:
        wc = clusters.get_words(e)
        wordcounts.append(wc)
        for w in wc.keys():
            if w not in wordlist: wordlist.append(w)

    words = [[] for i in range(len(wordcounts))]

    for i, wc in enumerate(wordcounts):
        for word in wordlist:
            if word in wc: c = float(wc[word])
            else: c = 0.0
            words[i].append(c)

    kcluster = clusters.kcluster(words)
    #logging.debug(kcluster)

    similalities = []
    for cluster in kcluster:
        for i, c in enumerate(cluster):
            if entries[c] == entry:
                #similalities = cluster
                similalities = [entries[cl] for cl in cluster]
                break
    #logging.debug(similalities)

    return render_to_response(request, 'feed/entry_detail.html',
                              {'entry' : entry, 'similalities' : similalities})

def entry_edit(request, key):
    return update_object(request, object_id=key, form_class=EntryForm)

def entry_delete(request, key):
    wordlist = WordList.all().filter('entry_ref =', Entry.get(key)).fetch(1000)
    for w in wordlist: w.delete()

    return delete_object(request, Entry, object_id=key,
        post_delete_redirect=reverse('feed.views.entry_list'))

def feature_list(request):
    entries = Entry.all().order('-created_at').fetch(50)
    feature_counts = [docclass.entryfeatures(e, 50, True) for e in entries]

    wordlist = {}
    for features in feature_counts:
        for f, c in features.items():
            wordlist.setdefault(f, 0)
            wordlist[f] += c

    wordlist = sorted(wordlist.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    return render_to_response(request, 'feed/feature_list.html',
                              {'wordlist' : wordlist[0:30], 'label' : u'Feature'})

def category_list(request):
    entries = Entry.all().order('-created_at').fetch(50)
    
    wordlist = {}
    for e in entries:
        for ec in e.entrycategory_set:
            wordlist.setdefault(ec.lower_category, 0)
            wordlist[ec.lower_category] += 1

    wordlist = sorted(wordlist.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    return render_to_response(request, 'feed/feature_list.html',
                              {'wordlist' : wordlist[0:30], 'label' : u'Category'})

def crawl(request):
    now = datetime.utcnow()
    feed_obj = Feed.all().filter('execute_hour =', now.hour).fetch(50)

    if now.minute <= 15:
        feeds = [f for f in feed_obj for em in f.execute_minute if em <= 15]
    elif now.minute <= 30:
        feeds = [f for f in feed_obj for em in f.execute_minute if em > 15 and em <= 30]
    elif now.minute <= 45:
        feeds = [f for f in feed_obj for em in f.execute_minute if em > 30 and em <= 45]
    else:
        feeds = [f for f in feed_obj for em in f.execute_minute if em > 45]

    classifier = docclass.naivebayes(docclass.entryfeatures)
    classifier.setthreshold('Google', 2.0)
    classifier.setthreshold('Apple', 2.0)
    classifier.setthreshold('Microsoft', 2.0)

    categories = []

    for feed in feeds:
        d = feedparser.parse(feed.url)
        markup = "_crawledurls_%s" % str(feed.key())
        cached_urls = cache.get(markup, [])

        i = 0
        for e in d.entries[0:7]:
            try:
                url_hash = hashlib.md5(e.link).hexdigest()
                if url_hash in cached_urls: continue
                entry = Entry.all().filter('url_hash =', url_hash).get()
                if entry: continue

                #summary
                if 'summary' in e: summary = e.summary
                elif 'description' in e: summary = e.description
                else: summary = ''

                entry = Entry(
                    feed_ref = feed.key(),
                    title = e.title,
                    url = e.link,
                    description = summary,
                    url_hash = url_hash)

                if not DEBUG and i < 5:
                    classifier.classify(entry, 'Unknown')
                    processing_time = classifier.get_processingtime()
                    logging.info('processing time >>> %s' % processing_time)
                    entry.cat_ref = classifier.getbestcat()
                    categories.append(entry.cat_ref.category)

                entry.save()

                if e.has_key('categories'):
                    for c in e.categories:
                        ec = EntryCategory(entry_ref=entry, orig_category=c[1], lower_category=c[1].lower())
                        ec.save()

                cached_urls.insert(0, url_hash)
                i += 1
            except StandardError, inst:
                logging.error('Failed to parse feed %s, %s' % (feed.url, inst))

        #Update cache
        del cached_urls[50:]
        cache.set(markup, cached_urls, 86400)

    #Delete cache
    if len(categories) > 0:
        catset = set(categories)
        for c in list(catset):
            cache.delete("%s_entries" % c)

    return HttpResponse()

def train(request, key):
    classifier = docclass.naivebayes(docclass.entryfeatures)
    entry = Entry.get(key)
    category = ""

    if request.method == 'POST':
        if 'word' in request.POST and request.POST.get('word') and request.POST.get('word') != '':
            category_count = classifier.train(entry, request.POST.get('word'))
            entry.cat_ref = category_count
            entry.is_trained = True
            entry.save()
            category = category_count.category
            cache.delete('%s_entries' % category)

    return JSONResponse({ 'category' : category })

def untrain(request, key):
    classifier = docclass.naivebayes(docclass.entryfeatures)
    entry = Entry.get(key)

    if request.method == 'POST':
        cache.delete('%s_entries' % entry.cat_ref.category)
        classifier.untrain(entry)
        entry.cat_ref = None
        entry.is_trained = False
        entry.save()
        return JSONResponse({'success' : 1})
    raise Http404()

def guess(request, key):
    classifier = docclass.naivebayes(docclass.entryfeatures)
    classifier.setthreshold('Google', 2.0)
    classifier.setthreshold('Apple', 2.0)
    classifier.setthreshold('Microsoft', 2.0)

    entry = Entry.get(key)

    category = classifier.classify(entry, 'unknown')
    processingtime = classifier.get_processingtime()

    return JSONResponse({
        'category' : category,
        'processingtime' : processingtime
        })

def refleshclassifier(request):
    classifier = docclass.naivebayes(docclass.getwords)
    classifier.testrun()
    return HttpResponse(mimetype='application/javascript')
