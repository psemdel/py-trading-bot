#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 23:07:32 2023

@author: maxime
"""

import unittest
from opt import opt_macro

import vectorbtpro as vbt

class TestOptMacro(unittest.TestCase):
    def test_macro(self):
        self.o=opt_macro.Opt("2007_2022_08",
                         loops=1)
        self.o.perf()



