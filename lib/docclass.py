from feed.models import *
import re, math


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
        self.fc = {}
        self.cc= {}
        self.getfeatures = getfeatures

    def incf(self, f, cat):
        count = self.fcount(f, cat)
        if count == 0:
            FeatureCount(feature=f, category=cat, count=1)
        else:
            feature = FeatureCount.all().filter('feature =', f).filter('category =', cat).get()
            if feature != None:
                feature.count += 1
                feature.save()
        '''self.fc.setdefault(f, {})
        self.fc[f].setdefault(cat, 0)
        self.fc[f][cat] += 1'''

    def incc(self, cat):
        count = self.catcount(cat)
        if count == 0:
            CategoryCount(category=cat, count=1)
        else:
            category_count = CategoryCount.all().filter('category =', cat).get()
            if category_count:
                category_count.count += 1
                category_count.save()
        '''self.cc.setdefault(cat, 0)
        self.cc[cat] += 1'''

    def fcount(self, f, cat):
        feature = FeatureCount.all().filter('feature =', f).filter('category =', cat).get()
        if feature: return float(feature.count)
        else: return 0
        '''if f in self.fc and cat in self.fc[f]:
            return float(self.fc[f][cat])
        return 0.0'''

    def catcount(self, cat):
        return CategoryCount.all().filter('category =', cat).count()
        '''if cat in self.cc:
            return float(self.cc[cat])
        return 0'''

    def totalcount(self):
        category_counts = CategoryCount.all().fetch(1000)
        count = 0
        for d in category_counts: count += d.count
        return count
        #return sum(self.cc.values())

    def categories(self):
        category_counts = CategoryCount.all().fetch(1000)
        return [d.category for d in category_counts]
        #return self.cc.keys()

    def train(self, item, cat):
        features = self.getfeatures(item)
        for f in features:
            self.incf(f, cat)
        self.incc(cat)

    def fprob(self, f, cat):
        if self.catcount(cat) == 0: return 0
        return self.fcount(f, cat) / self.catcount(cat)

    def weightedprob(self, f, cat, prf, weight=1.0, ap=0.5):
        basicprob = prf(f, cat)
        totals = sum([self.fcount(f, c) for c in self.categories()])

        return ((weight*ap) + (totals*basicprob)) / (weight+totals)


class naivebayes(classifier):

    def __init__(self, getfeatures):
        classifier.__init__(self, getfeatures)
        self.thresholds = {}

    def docprob(self, item, cat):
        features = self.getfeatures(item)
        p = 1
        for f in features: p *= self.weightedprob(f, cat, self.fprob)
        return p

    def prob(self, item, cat):
        catprob = self.catcount(cat) / self.totalcount()
        docprob = self.docprob(item, cat)
        return docprob * catprob

    def setthreshold(self, cat, t):
        self.thresholds[cat] = t

    def getthreshold(self, cat):
        if cat not in self.thresholds: return 1.0
        return self.thresholds[cat]

    def classify(self, item, default=None):
        probs = {}
        max = 0.0
        for cat in self.categories():
            probs[cat] = self.prob(item, cat)
            if probs[cat] > max:
                max = probs[cat]
                best = cat

        for cat in probs:
           if cat == best: continue
           if probs[cat]*self.getthreshold(best) > probs[best]: return default
        return best


