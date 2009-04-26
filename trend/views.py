# -*- coding: utf-8 -*-
from django.http import HttpResponse, Http404
from trend.forms import PersonForm
from trend.models import Contract, File, Person
from ragendja.template import render_to_response
from django.core.cache import cache
from xml.dom.minidom import parseString
from google.appengine.api import urlfetch
from lib import boss, feedparser
import urllib, re, sha, logging

def index(request):
    return render_to_response(request, 'trend/index.html', {})


def list(request):
    trends = googletrend()
    payload = dict(trends=trends)
    return render_to_response(request, 'trend/list.html', payload)

def show(request, query):
    query = urllib.unquote_plus(query)
    trends = googletrend()[0:20]
    blogs = blog_search(query)
    sites = boss.WebSearch().get(query)
    adsense = True if len(blogs) > 15 else False

    payload = dict(trends=trends, blogs=blogs, sites=sites, query=query, adsense=adsense)
    return render_to_response(request, 'trend/show.html', payload)

def sitemap(request):
    trends = googletrend()
    payload = dict(trends=trends)
    return render_to_string('trend/sitemap.xml', payload)


def googletrend():
    cache_key = "newsy-index"
    trends = cache.get(cache_key)

    if not trends:
        url = "http://www.google.com/trends/hottrends/atom/hourly"
        res = urlfetch.fetch(url)
        trends = []
        if res.status_code == 200:
            r = re.compile('<li><span class=".+"><a href=".+">(.+)</a></span></li>')
            for m in r.findall(res.content):
                trends.append(m)
            cache.set(cache_key, trends, 3600)
    return trends

def blog_search(query):
    cache_key = "newsy-blog-" + sha.new(query).hexdigest()
    entries = cache.get(cache_key)

    if entries == None:
        url = "http://blogsearch.google.co.jp/blogsearch_feeds?"
        params = {
            'hl' : 'en', 
            'q' : query,
            'lr' : 'lang_en',
            'ie' : 'utf-8',
            'num'  : 25,
            'output' : 'rss'}

        d = feedparser.parse(url + urllib.urlencode(params))
        entries = []
        for e in d.entries:
            if 'summary' in e: summary = e.summary
            else: summary = e.description
            entries.append({
                'title' : e.title,
                'link' : e.link,
                'description' : e.summary
            })

    return entries
