# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext as __
from feed.models import *
from ragendja.forms import FormWithSets, FormSetField

class FeedForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs=dict(maxlength=75)),
        label=_(u'Feed Name'))
    url = forms.URLField(widget=forms.TextInput(attrs=dict(maxlength=75)),
         label=_(u'Feed URL'))

    class Meta:
        model = Feed
        exclude = ['created_at', 'updated_at']

