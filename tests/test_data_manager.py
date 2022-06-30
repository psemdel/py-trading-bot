#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 17:03:49 2022

@author: maxime
"""

import unittest
from core import data_manager
import numpy as np

class TestIndicator(unittest.TestCase):
    def test_retrieve(self):
        high, low, close, open_, volume, high_ind, low_ind, close_ind, open_ind, volume_ind=\
            data_manager.retrieve("CAC40","2007_2009")
            
        self.assertEqual(np.shape(high)[0],511)
        self.assertEqual(np.shape(low)[0],511)
        self.assertEqual(np.shape(open_)[0],511)
        self.assertEqual(np.shape(close)[0],511)  
        self.assertEqual(np.shape(volume)[0],511)
        self.assertEqual(np.shape(high_ind)[0],511)
        self.assertEqual(np.shape(low_ind)[0],511)
        self.assertEqual(np.shape(open_ind)[0],511)
        self.assertEqual(np.shape(close_ind)[0],511)        
        self.assertEqual(np.shape(volume_ind)[0],511)  
          
        self.assertEqual(np.shape(high)[1],26)
        self.assertEqual(np.shape(low)[1],26)
        self.assertEqual(np.shape(open_)[1],26)
        self.assertEqual(np.shape(close)[1],26)   
        self.assertEqual(np.shape(volume)[1],26)
  

        high, low, close, open_, volume, high_ind, low_ind, close_ind, open_ind, volume_ind=\
            data_manager.retrieve("DAX","2007_2022")
            
        self.assertEqual(np.shape(high)[0],3800)
        self.assertEqual(np.shape(low)[0],3800)
        self.assertEqual(np.shape(open_)[0],3800)
        self.assertEqual(np.shape(close)[0],3800)  
        self.assertEqual(np.shape(volume)[0],3800)
        self.assertEqual(np.shape(high_ind)[0],3800)
        self.assertEqual(np.shape(low_ind)[0],3800)
        self.assertEqual(np.shape(open_ind)[0],3800)
        self.assertEqual(np.shape(close_ind)[0],3800)        
        self.assertEqual(np.shape(volume_ind)[0],3800)  
          
        self.assertEqual(np.shape(high)[1],23)
        self.assertEqual(np.shape(low)[1],23)
        self.assertEqual(np.shape(open_)[1],23)
        self.assertEqual(np.shape(close)[1],23)   
        self.assertEqual(np.shape(volume)[1],23)

if __name__ == '__main__':
    unittest.main()
