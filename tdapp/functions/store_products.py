import logging
import sys
from pathlib import Path

try:
    from ..core.utilities import Utilities
except ImportError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from tdapp.core.utilities import Utilities

class store_products:

    def __init__(self) -> None:
        pass

    @property
    def limit_count(self) ->int:
        return 10
    
    def get_items_list(self, store_id=None, user_ingredients:list[str]=None, category:list[str]=[]) -> list:
        """Get a comma-separated list of available products for a store.
        
        Combines Meijer products with optional user-suggested ingredients, removing duplicates.
        Returns up to 10 items total, prioritizing user ingredients when provided.
        
        Args:
            store_id: Optional store identifier to filter products
            user_ingredients: Optional list of ingredients to include alongside Meijer products
            category: Optional list of product categories to filter by (e.g., 'produce', 'meat')
        
        Returns:
            List of product names (max 10 items)
            Returns error message if an exception occurs
        """
        try:             
            print(f"store_id: {store_id}, user_ingredients: {user_ingredients}, category: {category}")   
            # Todo: logic to read store specific produce items under promo / excess / frequently sold
            # pdt_file="meijer_products.csv"
            mjr_pdts = Utilities().get_store_products(store_id, category)
            
            if user_ingredients:
                # remove duplicates if present in user cart as well as meijer products
                combined_pdts = user_ingredients + [pdt['product'] for pdt in mjr_pdts if pdt['product'] not in user_ingredients]
                return combined_pdts[:self.limit_count]
            else:
                return [pdt['product'] for pdt in mjr_pdts[:self.limit_count]]
        except Exception as e:
            logging.error(f"Exception in get_items_list : {e}")
            return str(e)
    

if __name__ == "__main__":
    ## validate get_items_list method
    val = store_products().get_items_list(21, ['tomatoes','ground beef', 'onions'], ['produce','meat'])
    print(val)
    ##
