import pandas as pd
import os
from pathlib import Path

class Utilities():

    def __init__(self) -> None:
        pass
    
    @property
    def sample_count(self) ->int:
        return 5
    
    def pathinfo(self):
        print(f'current dir - {os.getcwd()}')
        # import sys
        # print(f'sys    path - {sys.path}')
        print(f'parent dir - {os.pardir}')
        print(f'parent dir abs path - {os.path.abspath(os.pardir)}')
        print(f'curr dir - {os.path.abspath(os.getcwd())}')
        print(f'joined path - {os.path.join(os.getcwd(), os.pardir)}')
        print(f'curr dir - {os.getcwd()}')
        print(f'curr dir abs path - {os.path.abspath(os.getcwd())}')
        print(f'FILE abs path  - {(os.path.abspath(__file__))}')
        print(f'FILE dir path  - {Path(os.path.dirname(__file__)).parent}')
        print(f'FILE real path  - {(os.path.realpath(__file__))}')

        print(f'joined path - {os.path.join(os.getcwd(), os.pardir)}')
        print(f'joined abs path - {os.path.abspath(os.path.join(os.getcwd(), os.pardir))}')
        

    def get_meijer_products(self, filename, storeid=None) -> list:
        input_file=filename
        
        df = pd.read_csv(os.path.join(Path(os.path.dirname(__file__)).parent, 'data', input_file), header=0)
        
        if storeid and storeid!=0:
            df=df[df['store']==storeid]
            
        d={'Y': 1, 'N': 0}
        df['isinpromotion']=df['isinpromotion'].map(d)
        
        df = df.sort_values(by=['inventory','isinpromotion'], ascending=[False, True])
        if df['product'].count()>0 :            
            pdt = df['product'].drop_duplicates().head(self.sample_count)
            return pdt
            # pdt_str = ', '.join(pdt)
            # return pdt_str
        else:
            return []

# ## validate get_meijer_products method
# val = Utilities().get_meijer_products('meijer_products.csv', None)
# print(val)
# ##

# Utilities().pathinfo()