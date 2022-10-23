#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 21:13:38 2022

@author: maxime
"""

from .models import Report
import django_filters
from django.forms.widgets import DateInput


class ReportFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='date',
                                       widget= DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                                       lookup_expr='gt', label='Start Date')
    end_date = django_filters.DateFilter(field_name='date',
                                         widget= DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                                         lookup_expr='lt', label='End Date')

    class Meta:
        model = Report
        fields = ['date', 'stock_ex', 'it_is_index', ]