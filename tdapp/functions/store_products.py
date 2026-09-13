import logging

# if __package__ in (None, ""):
#     import sys
#     from pathlib import Path
#     sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
#     from tdapp.core.utilities import Utilities
# else:
from ..core.utilities import Utilities

class store_products():

    def __init__(self) -> None:
        pass

    @property
    def limit_count(self) ->int:
        return 10
    
    def get_items_list(self, store_id=None, user_ingredients:list[str]=None, category:list[str]=[]) -> str:
        """Get the ingredients as comma separated string using Meijer products and user suggested items if specified"""
        try:                
            # Todo: logic to read store specific produce items under promo / excess / frequently sold
            pdt_file="meijer_products.csv"
            mjr_pdts = Utilities().get_meijer_products(pdt_file, store_id, category)
            
            if user_ingredients:
                # remove duplicates if present in user cart as well as meijer products
                combined_pdts = user_ingredients.split(', ') + [i for i in mjr_pdts if i not in user_ingredients.split(', ')]
                return ', '.join(combined_pdts[:self.limit_count])
            else:
                return ', '.join(mjr_pdts[:self.limit_count])
        except Exception as e:
            logging.error(f"Exception in get_items_list : {e}")
            return str(e)
    

## validate get_items_list method
val = store_products().get_items_list(21, None, ['produce','meat'])
print(val)
##