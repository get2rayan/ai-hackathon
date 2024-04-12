from ..core.utilities import Utilities
import logging

class recipes():

    def __init__(self) -> None:
        pass

    @property
    def limit_count(self) ->int:
        return 5
    
    def get_items_for_recipe(self, storeid, user_ingredients) -> str:
        """Get the ingredients as comma separated string using Meijer products and user suggested items if specified"""
        try:                
            # Todo: logic to read store specific produce items under promo / excess / frequently sold
            pdt_file="meijer_products.csv"
            mjr_pdts = Utilities().get_meijer_products(pdt_file, storeid)
            
            if user_ingredients:
                # remove duplicates if present in user cart as well as meijer products
                combined_pdts = user_ingredients.split(', ') + [i for i in mjr_pdts if i not in user_ingredients]
                return ', '.join(combined_pdts[:self.limit_count])
            else:
                return ', '.join(mjr_pdts)
        except Exception as e:
            logging.error(f"Exception in get_recipe : {e}")
            return e    
    

# ## validate get_meijer_products method
# val = get_items_for_recipe(21, None)
# print(val)
# ##