from django.contrib import admin
from feed.models import *
from feed.forms import *

class FeedAdmin(admin.ModelAdmin):
    #inlines = (EntryInline,)
    list_display = ('name', 'url', 'execute_hour', 'execute_minute')
    date_hierarchy = 'created_at'
    form = FeedForm

admin.site.register(Feed, FeedAdmin)

class EntryAdmin(admin.ModelAdmin):
    list_display = ('cat_ref', 'title', 'url', 'created_at')
    date_hierarchy = 'created_at'
    form = EntryForm

admin.site.register(Entry, EntryAdmin)

class FeatureCountAdmin(admin.ModelAdmin):
    list_display = ('feature', 'category', 'count',)

admin.site.register(FeatureCount, FeatureCountAdmin)

class EntryCategoryAdmin(admin.ModelAdmin):
    list_display = ('key', 'lower_category', 'orig_category',)

admin.site.register(EntryCategory, EntryCategoryAdmin)

