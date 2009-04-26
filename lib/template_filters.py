# -*- coding: utf-8; -*-
# import the webapp module
from google.appengine.ext import webapp
import re, urllib, cgi

# get registry, we need it to register our filter later.
register = webapp.template.create_template_register()

def class_name(value, page_type):
    cn = 'unselect'
    if(value == page_type):
        cn = 'selected'
    return cn

register.filter(class_name)

def username(user):
    if not user:
        return 'Anonymous'
    return cgi.escape(user.name)

register.filter(username)

def paginate(obj):
    if obj['count'] < obj['limit']:
        return ''
    query = ""
    if obj['query'] and obj['query'].has_key('page'):
        del obj['query']['page']
    if obj['query']:
        query = "&" + obj['query'].urlencode()

    res = '<div class="pagination">'
    if obj['page'] != 1:
        link = obj['link'] + '?page=' + str(obj['page'] - 1) + query
        res += '<a href="' + link + '">&#171; 前へ</a>'
    else:
        res += '<span class="disabled">&#171; 前へ</span>'

    if obj['count'] > (obj['limit'] * obj['page']):
        link = obj['link'] + '?page=' + str(obj['page'] + 1) + query
        res += ' <a href="' + link + '">次へ &#187;</a>'
    else:
        res += ' <span class="disabled">次へ &#187;</span>'
    res += '</div>'
    return res

register.filter(paginate)

def substr(value, length=60):
    if len(value) > length:
        return value[0 : length] + "..."
    else:
        return value

register.filter(substr)

def urlencode2(value):
    value = value.encode('utf-8')
    return urllib.quote_plus(value)

register.filter(urlencode2)

def to_link(value, search_index):
    tags = []

    for v in re.split(r'/|;', value):
        v = v.encode('utf-8').strip()
        quote_tag = urllib.quote_plus(v)
        #tag = cgi.escape(v)
        link = '<a href="/name/%s/%s" class="name">%s</a>' % (search_index.encode('utf-8'), quote_tag, v)
        tags.append(link)
    return ', '.join(tags)

register.filter(to_link)

def split_tags(value=[], username=None):
    tags = []
    if username: username = username.encode('utf-8')
    for v in value:
        v = v.encode('utf-8').strip()
        quote_tag = urllib.quote_plus(v)
        tag = cgi.escape(v)
        if username:
            link = '<a href="/user/%s/tag/%s" class="green">%s</a>' % (username, quote_tag, tag)
        else:
            link = '<a href="/tag/%s" class="green">%s</a>' % (quote_tag, tag)
        tags.append(link)
    return ', '.join(tags)

register.filter(split_tags)

