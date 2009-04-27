# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext as __
from feed.models import *
from ragendja.forms import FormWithSets, FormSetField
import logging

class FeedForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs=dict(maxlength=75)),
        label=_(u'Feed Name'))
    url = forms.URLField(widget=forms.TextInput(attrs=dict(maxlength=75)),
         label=_(u'Feed URL'))

    HOURS = [(i+1,i+1) for i in range(24)]
    execute_hour = forms.MultipleChoiceField(label=_(u'Hours'), 
        widget=forms.CheckboxSelectMultiple, choices=HOURS)

    MINUTES = [(i+1,i+1) for i in range(60)]
    execute_minute = forms.MultipleChoiceField(label=_(u'Minutes'), 
        widget=forms.CheckboxSelectMultiple,choices=MINUTES)

    def clean_execute_hour(self):
        logging.info("EXECUTE_HOUR >>> % s", self.cleaned_data['execute_hour'])
        execute_hour = self.cleaned_data['execute_hour']
        return [int(eh.strip()) for eh in execute_hour]

    def clean_execute_minute(self):
        execute_minute = self.cleaned_data['execute_minute']
        return [int(em.strip()) for em in execute_minute]

    class Meta:
        model = Feed
        exclude = ['created_at', 'updated_at']

