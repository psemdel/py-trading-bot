#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 23:28:20 2023

@author: maxime
"""


import unittest
from opt import opt_by_part

class TestOptByPart(unittest.TestCase):
    def test_by_part(self):
        self.o=opt_by_part.Opt("2007_2022_08",
                         loops=1)
        self.o.outer_perf()   

