import pandas as pd

class Utilities():

    def __init__(self) -> None:
        pass

    def get_meijer_products(self, filename, storeid=None) -> str:
        input_file=filename
        df = pd.read_csv(input_file, header=0)

        if storeid and storeid!=0:
            df=df[df['store']==storeid]
            
        d={'Y': 1, 'N': 0}
        df['isinpromotion']=df['isinpromotion'].map(d)
        
        df = df.sort_values(by=['inventory','isinpromotion'], ascending=[False, True])
        if df['product'].count()>0 :            
            pdt = df['product'].drop_duplicates().head(5)
            pdt_str = ', '.join(pdt)
            return pdt_str
        else:
            return ''

# ## validate get_meijer_products method
# val = Utilities().get_meijer_products("meijer_products.csv", None)
# print(val)
# ##