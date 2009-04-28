# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from google.appengine.ext import db
from ragendja.dbutils import cleanup_relations

class Feed(db.Model):
    name = db.StringProperty(required=True)
    url = db.LinkProperty(required=True)
    execute_hour = db.ListProperty(item_type=int)
    execute_minute = db.ListProperty(item_type=int)
    created_at = db.DateTimeProperty(auto_now_add = 1)
    updated_at = db.DateTimeProperty(auto_now_add = 1)

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        return ('feed.views.show', (), {'key': self.key()})

signals.pre_delete.connect(cleanup_relations, sender=Feed)

class Entry(db.Model):
    feed_ref = db.ReferenceProperty(Feed)
    title = db.StringProperty()
    url = db.LinkProperty()
    description = db.TextProperty()
    url_hash = db.StringProperty()
    created_at = db.DateTimeProperty(auto_now_add = 1)
    updated_at = db.DateTimeProperty(auto_now_add = 1)

    def __unicode__(self):
        return self.feed_ref.name

class Word(db.Model):
    word = db.StringProperty()
    apcount = db.IntegerProperty(default = 0)

    def __unicode__(self):
        return self.word

class WordList(db.Model):
    entry_ref = db.ReferenceProperty(Entry)
    word_ref = db.ReferenceProperty(Word)

    def __unicode__(self):
        return "[%s] %s" % (self.entry_ref.title, self.word_ref.word)

class Crawl(db.Model):
    feed_ref = db.ReferenceProperty(Feed)
    add_count = db.IntegerProperty(default = 0)
    created_at = db.DateTimeProperty(auto_now_add = 1)
    updated_at = db.DateTimeProperty(auto_now_add = 1)

    def __unicode__(self):
        return self.feed_ref.name


class EntryDuplicateError(Exception):
     def __init__(self, value):
         self.value = value

     def __str__(self):
         return repr(self.value)

