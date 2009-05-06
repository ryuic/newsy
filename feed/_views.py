# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from feed.forms import *
from feed.models import *
from ragendja.auth.decorators import staff_only
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response
from datetime import datetime
from lib import feedparser, docclass, clusters
import logging, re, md5

#@staff_only
def index(request):
    return object_list(request, Feed.all().order('-created_at'), paginate_by=10)

def show(request, key):
    #feed = get_object_or_404(Feed, key)
    feed = Feed.get(key)
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

def entry_list(request, key=None):
    payload = {'feed' : None}
    entries = Entry.all()
    if key:
        feed = get_object_or_404(Feed, key)
        entries.filter('feed_ref =', feed)
        payload['feed'] = feed
    entries.order('-created_at')

    return object_list(request, entries, paginate_by=25, extra_context=payload)

def entry_show(request, key):
    return object_detail(request, Entry.all(), key)

def entry_edit(request, key):
    return update_object(request, object_id=key, form_class=EntryForm)

def entry_delete(request, key):
    wordlist = WordList.all().filter('entry_ref =', Entry.get(key)).fetch(1000)
    for w in wordlist: w.delete()

    return delete_object(request, Entry, object_id=key,
        post_delete_redirect=reverse('feed.views.entry_list'))

def crawl(request):
    now = datetime.now()
    feeds = Feed.all() \
        .order('-created_at').fetch(1)
    #    .filter('execute_hour =', now.hour) \
    #    .filter('execute_minute =', now.minute) \
    #    .fetch(100)

    entries = []

    for feed in feeds:
        logging.info("Start Crawl >>> %s, [%d:%d %d]" % (feed.url, now.hour, now.minute, now.second))
        d = feedparser.parse(feed.url)
        for e in d.entries:
            try:
                url_hash = md5.new(e.link).hexdigest()
                entry = Entry.all().filter('url_hash =', url_hash).get()
                if entry: continue

                if 'summary' in e: summary = e.summary
                elif 'description' in e: summary = e.description
                else: summary = ''

                entry = Entry(
                    feed_ref = feed.key(),
                    title = e.title,
                    url = e.link,
                    description = summary,
                    url_hash = url_hash)
                entry.save()
                entries.append(entry)
            except StandardError, inst:
                logging.error('Failed to parse feed %s, %s' % (feed.url, inst))
        logging.info("End Crawl >>> %s, [%d:%d %d]" % (feed.url, now.hour, now.minute, now.second))

    return HttpResponse()
    #return render_to_response(request, 'feed/crawl.html', 
    #    {'feeds' : feeds, 'entries' : entries})

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

    return HttpResponse(simplejson.dumps({ 'category' : category }), 
            mimetype='application/javascript')

def untrain(request, key):
    classifier = docclass.naivebayes(docclass.entryfeatures)
    entry = Entry.get(key)

    if request.method == 'POST':
        classifier.untrain(entry)
        entry.cat_ref = None
        entry.is_trained = False
        entry.save()

    return HttpResponse(mimetype='application/javascript')

def guess(request, key):
    classifier = docclass.naivebayes(docclass.entryfeatures)
    entry = Entry.get(key)
    classifier.setthreshold('Mozilla', 3.0)
    start = datetime.now()
    category = classifier.classify(entry, 'unknown')
    end = datetime.now()
    processingtime = (end - start).seconds
    return HttpResponse(simplejson.dumps({
        'category' : category,
        'processingtime' : processingtime,
        'start' : '%s:%s %s' % (start.hour, start.minute, start.second),
        'end' : '%s:%s %s' % (end.hour, end.minute, end.second)
        }), 
        mimetype='application/javascript')

def refleshclassifier(request):
    classifier = docclass.naivebayes(docclass.getwords)
    classifier.testrun()
    return HttpResponse(mimetype='application/javascript')

def scan(request):
    entries = Entry.all().filter('is_scanned =', False).order('-created_at').fetch(15)
    wordcounts, apcount = {}, {}

    for e in entries:
        wc = getwordcounts(e)
        wordcounts[e] = wc

        #apcountの集計
        for word, count in wc.items():
            apcount.setdefault(word, 0)
            if count > 1: apcount[word] += 1

    wordlist = []
    for w, bc in apcount.items():
        frac = float(bc) / len(entries)
        if frac > 1.0 and frac < 0.5: wordlist.append(w)

    for entry, wc in wordcounts.items():
        for word, count in wc.items():
            if not word in wordlist: continue

            #Datastore
            w = Word.all().filter('word =', word).get()
            if not w: w = Word(word=word, apcount=count)
            else: w.apcount += count
            w.save()
            wl = WordList(entry_ref=entry, word_ref=w, apcount=count).save()
        entry.is_scanned = True
        entry.save()

    return render_to_response(request, 'feed/scan.html',  {'entries' : entries})

def _crawl(request):
    now = datetime.now()
    feeds = Feed.all() \
        .order('-created_at').fetch(1)
    #    .filter('execute_hour =', now.hour) \
    #    .filter('execute_minute =', now.minute) \
    #    .fetch(100)

    apcount = {}
    wordcounts = {}
    entry_count = 0

    for feed in feeds:
        logging.info("Start Crawl >>> %s, [%d:%d %d]" % (feed.url, now.hour, now.minute, now.second))
        d = feedparser.parse(feed.url)
        for e in d.entries[6:]:
            try:
                entry, wc = getwordcounts(feed, e)
                wordcounts[entry] = wc

                #apcountの集計
                for word, count in wc.items():
                    apcount.setdefault(word, 0)
                    if count > 1: apcount[word] += 1

                entry_count += 1
            except EntryDuplicateError:
                pass
            except StandardError, inst:
                logging.error('Failed to parse feed %s, %s' % (feed.url, inst))
        logging.info("End Crawl >>> %s, [%d:%d %d]" % (feed.url, now.hour, now.minute, now.second))

    logging.debug('entry_count >>>>> %s' % entry_count)

    wordlist = []
    for w, bc in apcount.items():
        frac = float(bc) / entry_count
        if frac > 0.07 and frac < 0.9: wordlist.append(w)

    results = []
    for entry, wc in wordcounts.items():
        result = {'blog' : feed.name, 'count' : []}

        for word, count in wc.items():
            if not word in wordlist: continue

            #Datastore
            w = Word.all().filter('word =', word).get()
            if not w: w = Word(word=word, apcount=count)
            else: w.apcount += count
            w.save()
            wl = WordList(entry_ref=entry, word_ref=w, apcount=count).save()

            result['count'].append(count)
        results.append(result)

    return render_to_response(request, 'feed/crawl.html', 
        {'feeds' : feeds, 'results' : results, 'wordlist' : wordlist})

def getwordcounts(e):
    wc = {}
    i = 0
    words = getwords(e.title + ' ' + e.description)
    for word in words:
        if i > 150: break
        wc.setdefault(word, 0)
        wc[word] += 1
        i += 1
    return wc

def _getwordcounts(feed, e):
    url_hash = md5.new(e.link).hexdigest()
    entry = Entry.all().filter('url_hash =', url_hash).get()
    if entry:
        raise EntryDuplicateError, '%s has been already add.' % e.link

    if 'media' in e: del e['media']
    if 'summary' in e: summary = e.summary
    else: summary = e.description

    wc = {}
    i = 0
    words = getwords(e.title + ' ' + summary)
    for word in words:
        if i > 150: break
        wc.setdefault(word, 0)
        wc[word] += 1
        i += 1

    entry = Entry(
        feed_ref = feed.key(),
        title = e.title,
        url = e.link,
        description = summary,
        url_hash = url_hash)
    entry.save()
    return entry, wc



