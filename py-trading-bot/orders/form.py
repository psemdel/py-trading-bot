#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 19:42:27 2023

@author: maxime
"""

from django import forms
from orders.models import Action, Strategy, ActionSector

class ManualOrderForm(forms.Form):
    action = forms.ModelChoiceField(queryset=Action.objects.all())
    strategy = forms.ModelChoiceField(queryset=Strategy.objects.all())
    TrueFalse=(
        (True, "True"),
        (False,"False")
        )
    short = forms.ChoiceField(choices=TrueFalse)
    sector= forms.ModelChoiceField(queryset=ActionSector.objects.all())