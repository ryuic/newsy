# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext as __
from feed.models import *
from ragendja.forms import FormWithSets, FormSetField
import logging

class FeedForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs=dict(maxlength=75)),
        label=_(u'Feed Name'))
    url = forms.URLField(widget=forms.TextInput(attrs=dict(maxlength=75)),
         label=_(u'Feed URL'))

    def clean_execute_hour(self):
        execute_hour = self.cleaned_data['execute_hour'].split(',');
        return [int(eh.strip()) for eh in execute_hour]

    def clean_execute_minute(self):
        execute_minute = self.cleaned_data['execute_minute'].split(',');
        return [int(em.strip()) for em in execute_minute]

    class Meta:
        model = Feed
        exclude = ['created_at', 'updated_at']

