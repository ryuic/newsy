from lib import feedparser
import re

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


apcount = {}
wordcounts = {}
feedlist = ['http://feeds.nytimes.com/nyt/rss/Technology', 'http://feedproxy.google.com/TechCrunch']

for feedurl in feedlist:
    try:
        title, wc = getwordcounts(feedurl)
        wordcounts[title] = wc
        for word, count in wc.items():
            apcount.setdefault(word, 0)
            if count > 1:
                apcount[word] += 1
    except:
        print 'Failed to parse feed %s' % feedurl

wordlist = []
for w, bcin in apcount.items():
    frac = float(bc) / len(feedlist)
    if flac > 0.1 and frac < 0.5: wordlist.append(w)
