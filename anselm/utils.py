from anselm.system import System

class Utils(System):
    
    def __init__(self):
        super().__init__()     

        self.log.info("utils")

    def extract_todo_pressure(self, doc):
            return doc.get('Calibration', {}).get('ToDo',{}).get('Values',{}).get('Pressure')
    
    def extract_target_pressure(self, doc):
        p_type = 'target_pressure'
        pressure = doc.get('Calibration', {}).get('Measurement',{}).get('Values',{}).get('Pressure')
        if pressure:
            for i, p in enumerate(pressure):
                print(p)
                if p.get('Type', '') == p_type:
                    break
            return p
        else:
            return {'Type':p_type, 'Unit': self.unit, 'Value':[]}
    
    def get_value(self, value_dict, unit):
        """todo format expr: '{:.1e}'
            ..todo::
                get conversion from db
        """
        if value_dict.get('Unit') == 'mbar' and self.unit == 'Pa':
            conv_factor = 100
        if value_dict.get('Unit') == 'Pa' and self.unit == 'Pa':
            conv_factor = 1

        return [v * conv_factor for v in self.ensure_float(value_dict.get('Value'))]

    def ensure_format(self, value_array): 
        if isinstance(value_array, list) and len(value_array) > 0:
            format_expr = '{:.1e}'
            return  [format_expr.format(v) for v in value_array]
        else:
            return value_array

    def ensure_float(self, form_array):
        if isinstance(form_array, list) and len(form_array) > 0:
            return [float(v) for v in form_array]
        else:
            return form_array

    def sort_pressure(self, form_pressure_acc, n_acc):
        float_arr = self.ensure_float(form_pressure_acc)
        sorted_zip_list = sorted(zip(float_arr, n_acc))
        return  self.ensure_format([v for v, _ in sorted_zip_list]),  [n for _, n in sorted_zip_list]

    def acc_pressure(self, value_dict,  form_pressure_acc, n_acc):
        """ Unit of pressure accumulator is self.unit
        """
        ok = ['Unit' in value_dict,
              'Value' in value_dict,
              isinstance(value_dict.get('Value'), list),
             ]
        if all(ok):
            form_array = self.ensure_format( self.get_value( value_dict , self.unit))
            n_array = value_dict.get('N', [1] * len(form_array))
            for i, form_value in enumerate(form_array):
                if not form_value in  form_pressure_acc:
                    form_pressure_acc.append(form_value)
                    n_acc.append(n_array[i])
                else:
                    j = form_pressure_acc.index(form_value)
                    if n_acc[j] < n_array[i]:
                        n_acc[j] = n_array[i]

            form_pressure_acc, n_acc = self.sort_pressure(form_pressure_acc, n_acc)
        else:
            self.log.error("value_dict is unsufficient {ok}".format(ok=ok))          
        return form_pressure_acc, n_acc, self.unit

    def remaining_pressure(self, value_dict, form_pressure_acc, n_acc):
        ok = ['Unit' in value_dict,
              'Value' in value_dict,
              isinstance(value_dict.get('Value'), list),
             ]
        remaining_pressure = []
        remaining_n = []
        if all(ok):
            form_pressure = self.ensure_format( self.get_value( value_dict , self.unit))
            for i, form_value in enumerate(form_pressure_acc):
                if not form_value in  form_pressure:
                    remaining_pressure.append(form_value)
                    remaining_n.append(n_acc[i])
                else:
                    n = form_pressure.count(form_value)
                    d = n_acc[i] - n
                    if d > 0:
                        remaining_pressure.append(form_value)
                        remaining_n.append(d)

        return remaining_pressure, remaining_n, self.unit