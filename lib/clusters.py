import random
from math import sqrt
import re, logging

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

def get_words(entry, wordcount=50):
    remover = re.compile(r'<[^>]+>')
    splitter = re.compile(r'[^A-Z^a-z]+')
    f = {}

    txt = remover.sub('', entry.title)
    title = splitter.split(txt)
    titlewords = [s.lower() for s in title
                    if len(s) > 3 and len(s) < 20 and s not in IGNOREWORDS]

    for w in titlewords:
        f.setdefault(w, 0)
        f[w] += 1

    txt = remover.sub('', entry.description)
    desc = splitter.split(txt)
    descwords = [s.lower() for s in desc[0:wordcount]
                    if len(s) > 3 and len(s) < 20 and s not in IGNOREWORDS]

    for i, w in enumerate(descwords):
        f.setdefault(w, 0)
        f[w] += 1

    return f

def peason(v1, v2):
    sum1 = sum(v1)
    sum2 = sum(v2)
    sum1Sq = sum([pow(v, 2) for v in v1])
    sum2Sq = sum([pow(v, 2) for v in v2])
    pSum = sum([v1[i] * v2[i] for i, d in enumerate(v1)])
    num = pSum - (sum1-sum2/len(v1))
    
    d1 = ((sum1Sq - pow(sum1, 2)) / len(v1))
    d2 = ((sum2Sq - pow(sum2, 2)) / len(v1))
    #den = sqrt(((sum1Sq - pow(sum1, 2)) / len(v1)) * (sum2Sq - pow(sum2, 2) / len(v1)))
    den = sqrt(d1 * d2)
    if den == 0: return 0
    return 1.0 - num/den

def kcluster(rows, distance=peason, k=4):
    word_length = len(rows[0])

    ranges = [(min([row[i] for row in rows]), max([row[i] for row in rows]))
        for i in range(word_length)]

    clusters = [[random.random() * (ranges[i][1] - ranges[i][0]) + ranges[1][0]
        for i in range(word_length)] for j in range(k)]

    lastmatches = None

    for t in range(100):
        bestmatches = [[] for i in range(k)]

        for j, row in enumerate(rows):
            bestmatch = 0
            for i in range(k):
                d = distance(clusters[i], row)
                if d < distance(clusters[bestmatch], row): bestmatch = i
            bestmatches[bestmatch].append(j)

        if bestmatches == lastmatches: break
        lastmatches = bestmatches

        for i in range(k):
            avgs = [0.0] * word_length
            if len(bestmatches[i]) > 0:
                for rowid in bestmatches[i]:
                    for m in range(len(rows[rowid])):
                        avgs[m] += rows[rowid][m]
                    for j in range(len(avgs)):
                        avgs[j] /= len(bestmatches[i])
                    clusters[i] = avgs
    return bestmatches
