# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from google.appengine.ext import db
from ragendja.dbutils import cleanup_relations

class FeatureCount(db.Model):
    feature = db.StringProperty()
    category = db.StringProperty()
    count = db.IntegerProperty(default = 1)

    def __unicode__(self):
        return self.feature

class CategoryCount(db.Model):
    category = db.StringProperty()
    count = db.IntegerProperty(default = 1)

    def __unicode__(self):
        return self.category

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
    cat_ref = db.ReferenceProperty(CategoryCount)
    title = db.StringProperty()
    url = db.LinkProperty()
    description = db.TextProperty()
    url_hash = db.StringProperty()
    is_trained = db.BooleanProperty(default = False)
    created_at = db.DateTimeProperty(auto_now_add = 1)
    updated_at = db.DateTimeProperty(auto_now_add = 1)

    def __unicode__(self):
        return self.title

    @permalink
    def get_absolute_url(self):
        return ('feed.views.entry_show', (), {'key': self.key()})

signals.pre_delete.connect(cleanup_relations, sender=Entry)

class EntryCategory(db.Model):
    entry_ref = db.ReferenceProperty(Entry)
    lower_category = db.StringProperty()
    orig_category = db.StringProperty()

    def __unicode__(self):
        return self.orig_category

class Word(db.Model):
    word = db.StringProperty()
    apcount = db.IntegerProperty(default = 0)

    def __unicode__(self):
        return self.word

class WordList(db.Model):
    entry_ref = db.ReferenceProperty(Entry)
    word_ref = db.ReferenceProperty(Word)
    apcount = db.IntegerProperty(default = 0)

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

