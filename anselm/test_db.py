import unittest
from .db import DB

class TestDB(unittest.TestCase):

    def setUp(self):
        self.db = DB()
        

    def test_doc_write_result_1(self):

        doc = {}
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.Values.Pressure", result={"Type":"a", "Value":1, "Unit":"Pa"})
        pressure = doc.get('Calibration').get('Measurement', {}).get('Values', {}).get('Pressure')
        self.assertTrue(isinstance(pressure, list))
        self.assertEqual(len(pressure), 1)
        self.assertTrue(isinstance(pressure[0].get('Value'), list))        
        self.assertEqual(pressure[0].get('Value')[0], 1)
        

    def test_doc_write_result_2(self):

        doc = {'Calibration': {'Measurement': {'Values': {'Pressure': [{'Type': 'a', 'Value': [1], 'Unit': 'Pa'}]}}}}
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.Values.Pressure", result={"Type":"a", "Value":2, "Unit":"Pa"})
        pressure = doc.get('Calibration').get('Measurement', {}).get('Values', {}).get('Pressure')
        self.assertTrue(isinstance(pressure, list))
        self.assertEqual(len(pressure), 1)
        self.assertTrue(isinstance(pressure[0].get('Value'), list))        
        self.assertEqual(pressure[0].get('Value')[0], 1)
        self.assertEqual(pressure[0].get('Value')[1], 2)
    
    def test_doc_write_result_3(self):

        doc = {'Calibration': {'Measurement': {'Values': {'Pressure': [{'Type': 'a', 'Value': [1], 'Unit': 'Pa'}]}}}}
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.Values.Pressure", result={"Type":"b", "Value":2, "Unit":"Pa"})
        pressure = doc.get('Calibration').get('Measurement', {}).get('Values', {}).get('Pressure')
        self.assertTrue(isinstance(pressure, list))
        self.assertEqual(len(pressure), 2)
        self.assertTrue(isinstance(pressure[0].get('Value'), list))        
        self.assertEqual(pressure[0].get('Value')[0], 1)
        self.assertEqual(pressure[1].get('Value')[0], 2)

    def test_doc_write_result_4(self):

        doc = {'Calibration': {'Measurement': {'AuxValues': {'Pressure': [{'Type': 'a', 'Value': [1], 'Unit': 'Pa'}]}}}}
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.AuxValues.Pressure", result={"Type":"offset_x1", "Value":[1,2,3], "Unit":"Pa"})
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.AuxValues.Pressure", result={"Type":"offset_x0.1", "Value":[4,5,6], "Unit":"Pa"})
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.AuxValues.Pressure", result={"Type":"offset_x0.01", "Value":[7,8,9], "Unit":"Pa"})
        pressure = doc.get('Calibration').get('Measurement', {}).get('AuxValues', {}).get('Pressure', {})
        self.assertEqual(len(pressure), 4)
        self.assertEqual(pressure[1].get('Value')[2], 3)
        self.assertEqual(pressure[2].get('Value')[2], 6)
        self.assertEqual(pressure[3].get('Value')[2], 9)
    
    def test_doc_write_result_5(self):
        """should override if len(value) > 1
        """
        doc = {'Calibration': {'Measurement': {'AuxValues': {}}}}
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.AuxValues.Pressure", result={"Type":"offset_x0.1", "Value":[1,2,3], "Unit":"Pa"})
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.AuxValues.Pressure", result={"Type":"offset_x0.1", "Value":[4,5,6], "Unit":"Pa"})
        pressure = doc.get('Calibration').get('Measurement', {}).get('AuxValues', {}).get('Pressure', {})
        self.assertEqual(len(pressure), 1)
        self.assertEqual(pressure[0].get('Value')[2], 6)
        self.db.doc_write_result(doc, doc_path="Calibration.Measurement.AuxValues.Pressure", result={"Type":"offset_x0.1", "Value":[7,8,9], "Unit":"Pa"})
        pressure = doc.get('Calibration').get('Measurement', {}).get('AuxValues', {}).get('Pressure', {})
        self.assertEqual(len(pressure), 1)
        self.assertEqual(pressure[0].get('Value')[2], 9)
    
    def test_last_target_pressure_1(self):
        doc = {}
        v, u = self.db.get_last_target_pressure(doc)
        self.assertEqual(v, None)
        self.assertEqual(u, None)

    def test_last_target_pressure_2(self):

        doc = {'Calibration': {'Measurement': {'Values': {'Pressure': [{'Type': 'target_pressure', 'Value': [1], 'Unit': 'Pa'}]}}}}
        v, u = self.db.get_last_target_pressure(doc)
        self.assertEqual(v, 1)
        self.assertEqual(u, 'Pa')
    
    def test_acc_todo_pressure_1(self):
        
        v, u = self.db.acc_todo_pressure([], {}, "Pa")
        self.assertEqual(len(v), 0)
        self.assertEqual(u, 'Pa')
    
    def test_acc_todo_pressure_2(self):
        """should sort 
        """
        doc = {'Calibration': {"ToDo": { "Values": { "Pressure": { "Type": "target", "Value": [
                                                                                                 "1.3", "0.13", "0.00013", "0.0013","0.013",
                                                                                                ],
                                                                                              "Unit": "mbar"
                                                                                            }}}}}
        v, u = self.db.acc_todo_pressure([], doc, "Pa")
        
        self.assertEqual(len(v), 5)
        self.assertEqual(v[0], '1.3e-02')
        self.assertEqual(v[4], '1.3e+02')        
        self.assertEqual(u, 'Pa')
    
    def test_acc_todo_pressure_2(self):
        """should fill in and sort
        """
        doc = {'Calibration': {"ToDo": { "Values": { "Pressure": { "Type": "target", "Value": [
                                                                                                 "0.00013", "0.0013","0.013",
                                                                                                ],
                                                                                              "Unit": "mbar"
                                                                                            }}}}}
        v, u = self.db.acc_todo_pressure([], doc, "Pa")
       
        doc = {'Calibration': {"ToDo": { "Values": { "Pressure": { "Type": "target", "Value": [
                                                                                                 "1.3", "0.13", "0.00013",
                                                                                                ],
                                                                                              "Unit": "mbar"
                                                                                            }}}}}
        v, u = self.db.acc_todo_pressure(v, doc, "Pa")
        self.assertEqual(len(v), 5)
        self.assertEqual(v[0], '1.3e-02')
        self.assertEqual(v[4], '1.3e+02')        
        self.assertEqual(u, 'Pa')