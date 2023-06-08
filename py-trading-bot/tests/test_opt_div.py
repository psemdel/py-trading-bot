#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 23:09:57 2023

@author: maxime
"""

import unittest
from opt import opt_div

class TestOptDiv(unittest.TestCase):
    def test_pressel(self):
        self.o=opt_div.Opt("2007_2022_08",
                         loops=1,
                         nb_macro_modes=3)
        self.o.perf()
