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
        data_manager.retrieve(self,"CAC40","2007_2009")
            
        self.assertEqual(np.shape(self.high)[0],511)
        self.assertEqual(np.shape(self.low)[0],511)
        self.assertEqual(np.shape(self.open)[0],511)
        self.assertEqual(np.shape(self.close)[0],511)  
        self.assertEqual(np.shape(self.volume)[0],511)
        self.assertEqual(np.shape(self.high_ind)[0],511)
        self.assertEqual(np.shape(self.low_ind)[0],511)
        self.assertEqual(np.shape(self.open_ind)[0],511)
        self.assertEqual(np.shape(self.close_ind)[0],511)        
        self.assertEqual(np.shape(self.volume_ind)[0],511)  
          
        self.assertEqual(np.shape(self.high)[1],26)
        self.assertEqual(np.shape(self.low)[1],26)
        self.assertEqual(np.shape(self.open)[1],26)
        self.assertEqual(np.shape(self.close)[1],26)   
        self.assertEqual(np.shape(self.volume)[1],26)
        self.assertEqual(len(np.shape(self.close_ind)),1)    

        data_manager.retrieve(self,"DAX","2007_2022")
            
        self.assertEqual(np.shape(self.high)[0],3800)
        self.assertEqual(np.shape(self.low)[0],3800)
        self.assertEqual(np.shape(self.open)[0],3800)
        self.assertEqual(np.shape(self.close)[0],3800)  
        self.assertEqual(np.shape(self.volume)[0],3800)
        self.assertEqual(np.shape(self.high_ind)[0],3800)
        self.assertEqual(np.shape(self.low_ind)[0],3800)
        self.assertEqual(np.shape(self.open_ind)[0],3800)
        self.assertEqual(np.shape(self.close_ind)[0],3800)        
        self.assertEqual(np.shape(self.volume_ind)[0],3800)  
          
        self.assertEqual(np.shape(self.high)[1],23)
        self.assertEqual(np.shape(self.low)[1],23)
        self.assertEqual(np.shape(self.open)[1],23)
        self.assertEqual(np.shape(self.close)[1],23)   
        self.assertEqual(np.shape(self.volume)[1],23)
        self.assertEqual(len(np.shape(self.close_ind)),1)    

if __name__ == '__main__':
    unittest.main()
