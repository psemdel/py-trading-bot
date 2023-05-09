#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  6 16:31:34 2022

@author: maxime
"""

from django.urls import path
from orders import views

app_name = 'orders'

urlpatterns = [ 
    path('portfolio/', views.pf_view, name="portfolio"),
    ]