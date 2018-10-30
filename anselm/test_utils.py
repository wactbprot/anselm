import unittest
from anselm.utils import Utils

class TestDB(unittest.TestCase):
    
    def setUp(self):
        self.utils = Utils()
        
    def test_acc_pressure_1(self):
        """should sort and generate N array
        """
        todo_dict = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "Unit": "mbar"
                     }
        N = len(todo_dict.get('Value'))
        v, n, u = self.utils.acc_pressure(todo_dict, [], [])
        
        self.assertEqual(u, 'Pa')
        self.assertEqual(len(v), N)
        self.assertEqual(len(v), len(n))
       
    def test_acc_pressure_2(self):
        """should sort with N array
        """
        todo_dict = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "N": [
                            1,2,5,4,3
                            ],
                       "Unit": "mbar"
                     }
        N = len(todo_dict.get('Value'))
        v, n, u = self.utils.acc_pressure(todo_dict, [], [])

        self.assertEqual(u, 'Pa')        
        self.assertEqual(len(v), N)
        self.assertEqual(len(v), len(n))
        self.assertEqual(v[0], "1.3e-02")
        self.assertEqual(n[0], 5)
        self.assertEqual(n[1], 4)
        self.assertEqual(n[2], 3)
        self.assertEqual(n[3], 2)
        self.assertEqual(n[4], 1)

    def test_acc_pressure_2(self):
        """should sort with N array
        """
        todo_dict = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "N": [
                            1,2,5,4,3
                            ],
                       "Unit": "mbar"
                     }
        N = len(todo_dict.get('Value'))
        v, n, u = self.utils.acc_pressure(todo_dict, [], [])

        self.assertEqual(u, 'Pa')        
        self.assertEqual(len(v), N)
        self.assertEqual(len(v), len(n))
        self.assertEqual(v[0], "1.3e-02")
       
    def test_acc_pressure_3(self):
        """should sort with N array and merge
        """
        todo_dict_1 = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "N": [
                            1,2,5,4,3
                            ],
                       "Unit": "mbar"
                     }
        todo_dict_2 = { "Type": "target", 
                      "Value": [
                                "2.3", "0.23", "0.00023", "0.0023","0.023",
                                ],
                       "N": [
                            1,2,5,4,3
                            ],
                       "Unit": "mbar"
                     }
        N = len(todo_dict_1.get('Value')) + len(todo_dict_2.get('Value'))
        v, n, u = self.utils.acc_pressure(todo_dict_1, [], [])
        v, n, u = self.utils.acc_pressure(todo_dict_2, v, n)
        self.assertEqual(u, 'Pa')        
        self.assertEqual(len(v), N)
        self.assertEqual(len(v), len(n))
        self.assertEqual(v[0], "1.3e-02")
        self.assertEqual(v[1], "2.3e-02")
        self.assertEqual(n[0], 5)
        self.assertEqual(n[1], 5)

    def test_acc_pressure_3(self):
        """should sort with N array and merge and update n_array
        """
        todo_dict_1 = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "N": [
                            1,1,1,1,1
                            ],
                       "Unit": "mbar"
                     }
        todo_dict_2 = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "N": [
                            3,1,3,1,1
                            ],
                       "Unit": "mbar"
                     }
        N = len(todo_dict_1.get('Value'))
        v, n, u = self.utils.acc_pressure(todo_dict_1, [], [])
        self.assertEqual(u, 'Pa')        
        self.assertEqual(len(v), len(n))
        self.assertEqual(n[0], 1)
        self.assertEqual(n[4], 1)
        
        v, n, u = self.utils.acc_pressure(todo_dict_2, v, n)
        self.assertEqual(len(v), N)
        self.assertEqual(v[0], "1.3e-02")
        self.assertEqual(n[0], 3)
        self.assertEqual(n[4], 3)
    
    def test_remaining_pressure_1(self):
        """should return remaining pressures
        """
        todo_dict = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "N": [
                            1,1,1,1,1
                            ],
                       "Unit": "mbar"
                     }
         
        target_dict = { "Type": "target_pressure", 
                      "Value": [
                                 0.013, 0.13, 1.3
                                ],
                       
                       "Unit": "Pa"
                     }           
        v, n, u = self.utils.acc_pressure(todo_dict, [], [])
        w, m, u = self.utils.remaining_pressure(target_dict, v,n)
        
        self.assertEqual(u, 'Pa')  
        self.assertEqual(len(w), len(m))
        self.assertEqual(len(w), 2)
        self.assertEqual(w[0], "1.3e+01")
        self.assertEqual(w[1], "1.3e+02")

    def test_remaining_pressure_2(self):
        """should return remaining pressures count n
        """
        todo_dict = { "Type": "target", 
                      "Value": [
                                "1.3", "0.13", "0.00013", "0.0013","0.013",
                                ],
                       "N": [
                            2,2,2,2,2
                            ],
                       "Unit": "mbar"
                     }
         
        target_dict = { "Type": "target_pressure", 
                      "Value": [
                                 0.013, 0.13, 1.3
                                ],
                       
                       "Unit": "Pa"
                     }           
        v, n, u = self.utils.acc_pressure(todo_dict, [], [])
        w, m, u = self.utils.remaining_pressure(target_dict, v,n)
        print(w)
        print(m)
        self.assertEqual(u, 'Pa')  
        self.assertEqual(len(w), len(m))
        self.assertEqual(len(w), 5)
        self.assertEqual(w[0], "1.3e-02")
        self.assertEqual(w[1], "1.3e-01")
        self.assertEqual(m[1], 1)
        self.assertEqual(m[1], 1)
        self.assertEqual(m[2], 1)
        self.assertEqual(m[3], 2)
        self.assertEqual(m[4], 2)
