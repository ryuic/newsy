from django.contrib import admin
from feed.models import *

#class FileInline(admin.TabularInline):
#    model = File

class FeedAdmin(admin.ModelAdmin):
    #inlines = (FileInline,)
    list_display = ('name', 'url')

admin.site.register(Feed, FeedAdmin)
