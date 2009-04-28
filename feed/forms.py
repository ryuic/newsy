# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext as __
from feed.models import *
from ragendja.forms import FormWithSets, FormSetField
#import logging

class FeedForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs=dict(maxlength=75)),
        label=_(u'Feed Name'))
    url = forms.URLField(widget=forms.TextInput(attrs=dict(maxlength=75)),
         label=_(u'Feed URL'))

    HOURS = [(i,i) for i in range(0, 24)]
    execute_hour = forms.MultipleChoiceField(label=_(u'Hours'), 
        widget=forms.CheckboxSelectMultiple, choices=HOURS)

    MINUTES = [(i,i) for i in range(0, 60)]
    execute_minute = forms.MultipleChoiceField(label=_(u'Minutes'), 
        widget=forms.CheckboxSelectMultiple,choices=MINUTES)

    def __init__(self, *args, **kwargs):
        self.auto_id = True
        super(forms.ModelForm, self).__init__(*args, **kwargs)


    def clean_execute_hour(self):
        execute_hour = self.cleaned_data['execute_hour']
        return [int(eh) for eh in execute_hour]

    def clean_execute_minute(self):
        execute_minute = self.cleaned_data['execute_minute']
        return [int(em) for em in execute_minute]

    class Meta:
        model = Feed
        exclude = ['created_at', 'updated_at']


class EntryForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(), label=_('Title'))
    url = forms.URLField(widget=forms.TextInput(), label=_(u'URL'))
    description = forms.CharField(widget=forms.Textarea(), label=_('Description'))

    def __init__(self, *args, **kwargs):
        self.auto_id = True
        super(forms.ModelForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Entry
        exclude = ['feed_ref', 'url_hash', 'created_at', 'updated_at']

