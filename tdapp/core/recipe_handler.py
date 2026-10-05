
import sys
from pathlib import Path
from tdapp.core.user_params import UserIntent
try:
    from .state import WorkflowState
except ImportError:
    from state import WorkflowState
try:
    from ..functions.store_products import store_products
except ImportError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from tdapp.functions.store_products import store_products


import json

class RecipeHandler:
    def __init__(self) -> None:
        pass

    @property
    def tools(self):
        return (
            [
                {
                    "type": "function",
                    "function":
                    {
                        "name": "get_items_list",
                        "description": "Get items from the store based on user input for item category",
                        "parameters": {
                            "type":"object",
                            "properties": {
                                "store_id": {
                                    "type": "integer",
                                    "description": "store id of Meijer store",
                                },
                                "user_ingredients": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description":"list of user ingredients."                                
                                },
                                "category":{
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description":"category of the items to fetch from the store."
                                }
                            },
                            "required": [],
                        }
                    }
                }
            ]
        )

    def get_recipe_items(self, user_intent: UserIntent)->list:
            # get user input from the workflow state
            if user_intent:
                store_id = user_intent.get('store_id')
                category = user_intent.get('category')
                user_ingredients = user_intent.get('user_ingredients')
            else:
                store_id = None
                category = None
                user_ingredients = None

            items_list = store_products().get_items_list(
                store_id=store_id,
                category=category,
                user_ingredients=user_ingredients
            )

            return items_list


    def get_custom_recipes(self, item_message ) -> str :
            # return item_message
            recipe_ingredients =None
            user_data = UserIntent.model_validate_json(item_message.content)
            print(f"user_data: {user_data}")
            
            # check if the model wanted to call a function
            if dict(item_message).get('tool_calls'):
                available_functions = {
                    "get_items_list": store_products().get_items_list
                }
                
                # extracting the functions
                for tool_call in item_message.tool_calls:
                    function_to_call = available_functions[tool_call.function.name]
                    function_args = json.loads(tool_call.function.arguments)
                    function_resp = function_to_call(**function_args)

                    print(f"function_args : {function_args} \n store_id :{user_data.store_id}  - category: {user_data.category} - user_ingredients: {user_data.user_ingredients} - recipe_name: {user_data.recipe_name} - serving_size: {user_data.serving_size}")
                    recipe_ingredients=function_resp    
            else:
                recipe_ingredients=store_products().get_items_list()

            print(f"recipe_ingredients : {recipe_ingredients}")

            messages=[
                        { "role": "system", "content": "You are an AI assistant that can suggest one recipe based on either the ingredients specified by the user and / or recipe name and / or serving size. Return recipe name, ingredients and instructions of the recipe in a json format. The ingredients that the user has should be under 'used_ingredients' and the ingredients that the user doesn't have should be under 'needed_ingredients'. Here is the example of your response format: {\"recipe\": "", \"user_ingredients\": "", \"needed_ingredients\", \"instructions\": ""}"}
                        ,{ "role": "user", "content": "How do I make moroccan meatballs when I have meatballs and oil"}
                        ,{ "role": "assistant", "content": "{\"recipe\": \"AlFez Moroccan Meatballs\",\"user_ingredients\": [\"Meatballs\",\"oil\"],\"needed_ingredients\": [\"AlFez  Moroccan Meatball Sauce\",\"Fresh coriander\",\"Cooked rice or couscous\"],\"instructions\":[\"1.\tIn a heated pan (or in the oven), brown the meatballs in oil, about 5 min.\"\r\n\"2.\tAdd the Al’FezTM Moroccan Meatball Sauce and simmer until the meatballs are cooked, about 20 min.\"\r\n\"3.\tServe over a be of rice or couscous. Garnish with fresh coriander.\"]}"}
                        ,{ "role": "user", "content": "How do I make make a meatball recipe for 4 people"}
                        ,{ "role": "assistant", "content": "{\"recipe\": \"AlFez Moroccan Meatballs\",\"needed_ingredients\": [\"12 Meatballs\",\"1 Tbsp Olive oil\",\"1 Jar AlFez  Moroccan Meatball Sauce\",\"Fresh coriander (for garnish)\",\"5 cups Cooked rice or couscous\"],\"instructions\":[\"1.\tIn a heated pan (or in the oven), brown the meatballs in oil, about 5 min.\"\r\n\"2.\tAdd the Al’FezTM Moroccan Meatball Sauce and simmer until the meatballs are cooked, about 20 min.\"\r\n\"3.\tServe over a be of rice or couscous. Garnish with fresh coriander.\"]}"}
                    ]

            recipe_name = user_data.recipe_name
            serving_size = user_data.serving_size

            print(f"recipe_name : {recipe_name} - serving_size: {serving_size} - recipe_ingredients: {recipe_ingredients}")
            if(recipe_name and serving_size and recipe_ingredients):
                user_intent = f"How do I make {recipe_name} for {serving_size} people when I have {recipe_ingredients}"
            elif (recipe_name and serving_size):
                user_intent = f"How do I make {recipe_name} for {serving_size} people"
            elif (recipe_name and recipe_ingredients):
                user_intent = f"How do I make {recipe_name} and I have {recipe_ingredients}"        
            elif (serving_size and recipe_ingredients):
                user_intent = f"Please suggest a recipe that I can make using {recipe_ingredients} and I need to prepare meal for {serving_size} people"
            elif (recipe_name):
                user_intent = f"How do I make {recipe_name}"
            elif (serving_size):
                user_intent = f"How do I make a meal for {serving_size} people"
            else:
                user_intent=f"Suggest a recipe that I can make using most of the following ingredients: {recipe_ingredients}"

            print (f"User intent : {user_intent}")
            user_prompt_message = { "role": "user", "content": user_intent }
            messages.append(user_prompt_message)

            recipe_response = self.client1.chat.completions.create(
                model=self.deploymentid,
                messages=messages,
                # past_messages=10,        
                # temperature=0.5,
                # extra_body={
                #     "data_sources": [
                #         {
                #             "type": "azure_search",
                #             "parameters": {
                #                 "endpoint": os.environ["SEARCH_ENDPOINT"],
                #                 "index_name": os.environ["SEARCH_INDEX_NAME"],
                #                 "semantic_configuration": "azureml_default",
                #                 "authentication": {
                #                     "type": "api_key",
                #                     "key": os.environ["SEARCH_API_KEY"]
                #                 }                            
                #             }
                #         }
                #     ]
                # }
            )

            # print(f"recipe response is {recipe_response}")
            recipe_message = recipe_response.choices[0].message
            print(recipe_message)
            return recipe_message.content


if __name__ == "__main__":
    recipe_handler = RecipeHandler()
    user_intent: UserIntent = {
        "store_id":21,
        "cuisine":"Mediterranean",
        "user_ingredients":["tomatoes","ground beef","onions"],
        "recipe_name":None,
        "serving_size":None,
        "category":["produce","meat"]
    }
    recipe_items = recipe_handler.get_recipe_items(user_intent)
    print(recipe_items)