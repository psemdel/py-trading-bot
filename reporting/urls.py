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
    path('actualize_hist_paris/',views.actualize_hist_paris,name="actualize_hist_paris"),
    path('actualize_hist_xetra/',views.actualize_hist_xetra,name="actualize_hist_xetra"),
    path('actualize_hist_nasdaq/',views.actualize_hist_nasdaq,name="actualize_hist_nasdaq"),
    path('actualize_realmadrid_paris/',views.actualize_realmadrid_paris,name="actualize_realmadrid_paris"),
    path('actualize_realmadrid_xetra/',views.actualize_realmadrid_xetra,name="actualize_realmadrid_xetra"),
    path('actualize_realmadrid_nasdaq/',views.actualize_realmadrid_nasdaq,name="actualize_realmadrid_nasdaq"),
    path('test/', views.test),
    path('17h/', views.trigger_17h,name="17h"),
    path('22h/', views.trigger_22h,name="22h"),
    path('cleaning/', views.cleaning,name="cleaning"),
    ]