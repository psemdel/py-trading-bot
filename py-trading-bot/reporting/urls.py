#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 29 15:23:49 2022

@author: maxime
"""

from django.urls import path
from reporting import views

app_name = 'reporting'

urlpatterns = [ 
    path('', views.reportsView, name="home"),
    path('daily/', views.dailyView),
    path('alerts/', views.alertsView, name="alerts"),
    path('reports/', views.reportsView, name="reports"),
    path('reports/<int:pk>', views.reportView, name='rep'),
    path('reports_trend/<int:pk>', views.trendView, name='trend'),
    path('start_bot/', views.start_bot, name="start_bot"),
    path('test/', views.test),
    path('17h/', views.trigger_17h,name="17h"),
    path('22h/', views.trigger_22h,name="22h"),
    path('cleaning/', views.cleaning,name="cleaning"),
    path('test_order/', views.test_order,name="test_order"),
    path('actualize_ss/',views.actualize_ss_view, name="actualize_ss")
    ]