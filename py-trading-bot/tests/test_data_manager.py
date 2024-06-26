#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 17:03:49 2022

@author: maxime
"""
from django.test import TestCase
from core.data_manager import retrieve_data_offline 
import numpy as np

class TestIndicator(TestCase):
    def test_retrieve(self):
        retrieve_data_offline(self,"CAC40","2007_2022_08")
            
        self.assertEqual(np.shape(self.data.get("High"))[0],4004)
        self.assertEqual(np.shape(self.high)[0],4004)
        self.assertEqual(np.shape(self.low)[0],4004)
        self.assertEqual(np.shape(self.open)[0],4004)
        self.assertEqual(np.shape(self.close)[0],4004)  
        self.assertEqual(np.shape(self.volume)[0],4004)
        self.assertEqual(np.shape(self.high_ind)[0],4004)
        self.assertEqual(np.shape(self.low_ind)[0],4004)
        self.assertEqual(np.shape(self.open_ind)[0],4004)
        self.assertEqual(np.shape(self.close_ind)[0],4004)        
        self.assertEqual(np.shape(self.volume_ind)[0],4004)  
          
        self.assertEqual(np.shape(self.high)[1],39)
        self.assertEqual(np.shape(self.low)[1],39)
        self.assertEqual(np.shape(self.open)[1],39)
        self.assertEqual(np.shape(self.close)[1],39)   
        self.assertEqual(np.shape(self.volume)[1],39)
        self.assertEqual(len(np.shape(self.close_ind)),1)    

        retrieve_data_offline(self,"DAX","2007_2022_08")
            
        self.assertEqual(np.shape(self.high)[0],3970)
        self.assertEqual(np.shape(self.low)[0],3970)
        self.assertEqual(np.shape(self.open)[0],3970)
        self.assertEqual(np.shape(self.close)[0],3970)  
        self.assertEqual(np.shape(self.volume)[0],3970)
        self.assertEqual(np.shape(self.high_ind)[0],3970)
        self.assertEqual(np.shape(self.low_ind)[0],3970)
        self.assertEqual(np.shape(self.open_ind)[0],3970)
        self.assertEqual(np.shape(self.close_ind)[0],3970)        
        self.assertEqual(np.shape(self.volume_ind)[0],3970)  
          
        self.assertEqual(np.shape(self.high)[1],31)
        self.assertEqual(np.shape(self.low)[1],31)
        self.assertEqual(np.shape(self.open)[1],31)
        self.assertEqual(np.shape(self.close)[1],31)   
        self.assertEqual(np.shape(self.volume)[1],31)
        self.assertEqual(len(np.shape(self.close_ind)),1)    
