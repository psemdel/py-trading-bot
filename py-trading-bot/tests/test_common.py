#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 17:03:49 2022

@author: maxime
"""

import unittest
from core import common
import numpy as np

class TestCommon(unittest.TestCase):
    def test_VBTfunc(self):
        v=common.VBTfunc("CAC40","2007_2009")
            
        self.assertEqual(np.shape(v.high)[0],511)
        self.assertEqual(np.shape(v.low)[0],511)
        self.assertEqual(np.shape(v.open)[0],511)
        self.assertEqual(np.shape(v.close)[0],511)  
        self.assertEqual(np.shape(v.volume)[0],511)
        self.assertEqual(np.shape(v.high_ind)[0],511)
        self.assertEqual(np.shape(v.low_ind)[0],511)
        self.assertEqual(np.shape(v.open_ind)[0],511)
        self.assertEqual(np.shape(v.close_ind)[0],511)        
        self.assertEqual(np.shape(v.volume_ind)[0],511)  
          
        self.assertEqual(np.shape(v.high)[1],26)
        self.assertEqual(np.shape(v.low)[1],26)
        self.assertEqual(np.shape(v.open)[1],26)
        self.assertEqual(np.shape(v.close)[1],26)   
        self.assertEqual(np.shape(v.volume)[1],26)


if __name__ == '__main__':
    unittest.main()
