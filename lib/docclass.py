from django.core.cache import cache
from datetime import datetime
from feed.models import *
import re, math,logging

IGNOREWORDS = [
    'about',
    'after',
    'almost',
    'along',
    'also',
    'another',
    'around',
    'away',
    'been',
    'before',
    'could',
    'days',
    'didn',
    'else',
    'ever',
    'every',
    'first',
    'from',
    'gets',
    'give',
    'have',
    'here',
    'into',
    'just',
    'know',
    'like',
    'long',
    'made',
    'many',
    'make',
    'might',
    'more',
    'only',
    'other',
    'said',
    'should ',
    'some',
    'sure',
    'that',
    'their',
    'these',
    'they',
    'this', 
    'think',
    'than',
    'then',
    'them',
    'there',
    'those',
    'time',
    'under',
    'very',
    'wasnt',
    'week',
    'well',
    'were',
    'will',
    'what ',
    'when',
    'which',
    'with',
    'would',
    'year',
    'your',
]

def entryfeatures(entry, wordcount=15):
    remover = re.compile(r'<[^>]+>')
    splitter = re.compile(r'[^A-Z^a-z]+')
    f = {}

    txt = remover.sub('', entry.title)
    title = splitter.split(txt)
    titlewords = [s.lower() for s in title
                    if len(s) > 3 and len(s) < 20 and s not in IGNOREWORDS]

    for w in titlewords: f['T: ' + w] = 1

    txt = remover.sub('', entry.description)
    desc = splitter.split(txt)
    descwords = [s.lower() for s in desc[0:wordcount]
                    if len(s) > 3 and s not in IGNOREWORDS]

    #uc = 0
    for i, w in enumerate(descwords):
        f[w] = 1
#        if w.isupper(): uc += 1
#
#        if i < len(descwords) - 1:
#            twowords = ' '.join(descwords[i:(i+2)])
#            f[twowords] = 1
#
#    if len(descwords) > 0 and float(uc) / len(descwords) > 0.3: f['UPPERCASE'] = 1
    return f

def getwords(doc):
    splitter = re.compile('\\W')
    words = [s.lower() for s in splitter.split(doc) if len(s) > 1 and len(s) < 20]
    return dict([(w, 1) for w in words])

def sampletrain(cl):
    cl.train('Nobody owes the water', 'good')
    cl.train('the quick rabbit jumps fences', 'good')
    cl.train('buy pharmaceuticals now', 'bad')
    cl.train("the quick brown fox jumps over the lazy dog", "good")
    cl.train("make quick money in the online casino", "bad")



class classifier:

    def __init__(self, getfeatures, filename=None):
        self.tcount = cache.get('tcount', 0)
        self.ftcount = cache.get('ftcount', {})
        self.fc = cache.get('fc', {})
        self.cc= cache.get('cc', {})
        self.getfeatures = getfeatures
        self.processingtime = 0
        #logging.debug("start:: tcount >>>>>>>> %d" % self.tcount)
        #logging.debug("start:: ftcount >>>>>>>> %d" % len(self.ftcount))
        #logging.debug("start:: fc >>>>>>>> %d" % len(self.fc))
        #logging.debug("start:: cc >>>>>>>> %d" % len(self.cc))

    def initialize(self):
        logging.debug("initialize class variables.")
        self.tcount = 0
        self.ftcount = {}
        self.fc = {}
        self.cc= {}

    def incf(self, f, cat):
        count = self.fcount(f, cat)
        if count == 0:
            ff = FeatureCount(feature=f, category=cat, count=1)
        else:
            ff = FeatureCount.all().filter('feature =', f).filter('category =', cat).get()
            if ff != None:
                ff.count += 1
        ff.save()

    def outcf(self, f, cat):
        count = self.fcount(f, cat)

        ff = FeatureCount.all().filter('feature =', f).filter('category =', cat).get()
        if ff:
            if ff.count == 1:
                ff.delete()
            elif ff.count > 1:
                ff.count -= 1
                ff.save()

    def incc(self, cat):
        count = self.catcount(cat)
        if count == 0:
            cc = CategoryCount(category=cat, count=1)
        else:
            cc = CategoryCount.all().filter('category =', cat).get()
            if cc:
                cc.count += 1
        cc.save()
        return cc

    def outcc(self, cat):
        cc = CategoryCount.all().filter('category =', cat).get()
        if cc:
            if cc.count == 1:
                cc.delete()
            elif cc > 1:
                cc.count -= 1
                cc.save()

    def fcount(self, f, cat):
        if f not in self.fc:
            self.fc.setdefault(f, {})
            self.fc[f].setdefault(cat, 0.0)
            fc = FeatureCount.all().filter('feature =', f).filter('category =', cat).get()
            if fc: self.fc[f][cat] = float(fc.count)
            #logging.debug("fcount not f - f = %s, cat = %s >>> %f" % (f, cat, self.fc[f][cat]))
        elif cat not in self.fc[f]:
            self.fc[f].setdefault(cat, 0.0)
            fc = FeatureCount.all().filter('feature =', f).filter('category =', cat).get()
            if fc: self.fc[f][cat] = float(fc.count)
            #logging.debug("fcount not cat - f = %s, cat = %s >>> %f" % (f, cat, self.fc[f][cat]))
        return self.fc[f][cat]

    def catcount(self, cat):
        if cat not in self.cc:
            self.cc.setdefault(cat, 0.0)
            cc = CategoryCount.all().filter('category =', cat).get()
            if cc: self.cc[cat] = float(cc.count)
            #logging.debug("catcount[%s] >>> %d" % (cat, self.cc[cat]))
        return self.cc[cat]

    def totalcount(self):
        if self.tcount == 0:
            category_counts = CategoryCount.all().fetch(50)
            count = 0
            for d in category_counts: count += d.count
            self.tcount = count
            #logging.debug("totalcount >>> %d" % self.tcount )
        return self.tcount

    def categories(self):
        category_counts = CategoryCount.all().fetch(50)
        return [d.category for d in category_counts]

    def train(self, entry, cat):
        self.initialize()

        features = self.getfeatures(entry, wordcount=100)
        for f in features:
            self.incf(f, cat)
        cc = self.incc(cat)
        return cc

    def untrain(self, entry):
        self.initialize()

        features = self.getfeatures(entry, wordcount=100)
        cat = entry.cat_ref.category
        for f in features:
            self.outcf(f, cat)
        self.outcc(cat)

    def fprob(self, f, cat):
        cc = self.catcount(cat)
        if cc == 0: return 0
        return self.fcount(f, cat) / cc

    def weightedprob(self, f, cat, prf, weight=1.0, ap=0.5):
        basicprob = prf(f, cat)
        #totals = sum([self.fcount(f, c) for c in self.categories()])

        if f not in self.ftcount:
            fc = FeatureCount.all().filter('feature =', f).fetch(1000)
            totals = sum([feature.count for feature in fc])
            self.ftcount[f] = totals
            #logging.debug("weightedprob[%s] >>> %d" % (f, totals))
        else:
            totals = self.ftcount[f]

        return ((weight*ap) + (totals*basicprob)) / (weight+totals)


class naivebayes(classifier):

    def __init__(self, getfeatures):
        classifier.__init__(self, getfeatures)
        self.thresholds = {}
        self.best = ''

    def docprob(self, features, cat):
        p = 1
        for f in features:
            p *= self.weightedprob(f, cat, self.fprob)
        return p

    def prob(self, features, cat):
        catprob = self.catcount(cat) / self.totalcount()
        docprob = self.docprob(features, cat)
        return docprob * catprob

    def setthreshold(self, cat, t):
        self.thresholds[cat] = t

    def getthreshold(self, cat):
        if cat not in self.thresholds: return 1.0
        return self.thresholds[cat]

    def classify(self, entry, default=None):
        start = datetime.now()
        probs = {}
        max = 0.0
        best = None
        features = self.getfeatures(entry)
        for cat in self.categories():
            probs[cat] = self.prob(features, cat)
            if probs[cat] > max:
                max = probs[cat]
                best = cat

        for cat in probs:
           if cat == best: continue
           if probs[cat]*self.getthreshold(best) > probs[best]: return default

        self.best = best
        end = datetime.now()
        self.processingtime = (end - start).seconds
        return best

    def testrun(self, cat='Javascript'):
        self.initialize()

        cache.delete('tcount')
        cache.delete('ftcount')
        cache.delete('fc')
        cache.delete('cc')

        probs = {}
        fc = FeatureCount.all().filter('category =', cat).fetch(150)
        features = dict([(f.feature, 1) for f in fc])

        for cat in self.categories():
            self.prob(features, cat)

        cache.set('tcount', self.tcount, 864000)
        cache.set('ftcount', self.ftcount, 864000)
        cache.set('fc', self.fc, 864000)
        cache.set('cc', self.cc, 864000)

    def getbestcat(self):
        #logging.debug('best cat >>>>>> %s' % self.best)
        return CategoryCount.all().filter('category =', self.best).get()

    def get_processingtime(self):
        return self.processingtime

