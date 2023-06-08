#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 23:09:05 2023

@author: maxime
"""

import unittest
from opt import opt_presel

import vectorbtpro as vbt

class TestOptPressel(unittest.TestCase):
    def test_pressel(self):
        self.o=opt_presel.Opt("2007_2022_08",
                         loops=1)
        self.o.perf()
