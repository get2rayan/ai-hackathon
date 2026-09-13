import os
import json
import logging
from openai import OpenAI
import dotenv
from ..functions import store_products

try:
    from .recipe_extraction import RecipeExtraction, StoreCategory
except ImportError:
    from recipe_extraction import RecipeExtraction, StoreCategory

dotenv.load_dotenv(override=True)


class Prompt():

    def __init__(self) -> None:        
        use_azure_active_directory = False  # Set this flag to True if you are using Azure Active Directory

        if not use_azure_active_directory:
            self.endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
            self.api_key = os.environ["AZURE_OPENAI_API_KEY"]
            # set the deployment model we want to use
            self.deploymentid =os.environ["DEPLOYMENT_NAME"]            
        
        # Generic AI client to extract information from user prompt
        self.client1 = OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key,
        )

        print(f"Azure OpenAI client initialized with endpoint: {self.endpoint} and deployment: {self.deploymentid}")

        # # AI extension client to work with custom Meijer data
        # self.client2 = openai.AzureOpenAI(
        #     base_url=f"{self.endpoint}/openai/deployments/{self.deploymentid}/extensions",
        #     api_key=self.api_key,
        #     api_version="2024-08-01-preview"
        # )

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

    def extractUserPrompt(self, userPrompt:str) -> str:
        print(f"User prompt received: {userPrompt}")
        # Below user prompt can signify 
        # 1. a user adding items to cart where the recipe will be based on their cart items / user uses smart devices for managing their shopping list
        # 2. meijer specific products chosen based on criteria at the store like items in promotion / high inventory items at the (can be store specific).
        system_prompt = """
        You are a data extraction assistant. Your job is to extract information from the user input and return them STRICTLY as a valid JSON object.
        If a category can be determined from the user input, use the 
        """
        system_message = [{ "role": "system", "content": system_prompt }]
        user_prompt_message = [{ "role": "user", "content": userPrompt }]

        messages = system_message + user_prompt_message
            
        try: 
            item_response = self.client1.chat.completions.create(
                model=self.deploymentid,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "recipe_extraction",
                        "strict": True,
                        "schema": RecipeExtraction.model_json_schema()
                    }
                },
                tools=self.tools,
                tool_choice= "auto" #{"type": "function", "function": { "name": "get_store_products"} }
            )
            
            item_message = item_response.choices[0].message
            return item_message
        
            # if item_message.tool_calls is not None:
            #     return item_message.tool_calls[0].function.arguments
            # else:
            #     return item_message.content
            
        except Exception as e:
            logging.exception(f"Exception in extractUserPrompt : {e}")        


    def get_custom_recipes(self, item_message ) -> str :
        # return item_message
        recipe_ingredients =None
        recipe_data = RecipeExtraction.model_validate_json(item_message.content)
        print(f"recipe_data: {recipe_data}")
        # print(f'item_message: {item_message}')
        # check if the model wanted to call a function
        if dict(item_message).get('tool_calls'):
            available_functions = {
                "get_items_list": store_products.recipes().get_items_list
            }
            
            # extracting the functions
            for tool_call in item_message.tool_calls:
                function_to_call = available_functions[tool_call.function.name]
                function_args = json.loads(tool_call.function.arguments)
                function_resp = function_to_call(**function_args)

                print(f"function_args : {function_args} \n store_id :{recipe_data.store_id}  - category: {recipe_data.category} - user_ingredients: {recipe_data.user_ingredients} - recipe_name: {recipe_data.recipe_name} - serving_size: {recipe_data.serving_size}")
                recipe_ingredients=function_resp    
        else:
            recipe_ingredients=store_products.recipes().get_items_list()

        print(f"recipe_ingredients : {recipe_ingredients}")

        messages=[
                    { "role": "system", "content": "You are an AI assistant that can suggest one recipe based on either the ingredients specified by the user and / or recipe name and / or serving size. Return recipe name, ingredients and instructions of the recipe in a json format. The ingredients that the user has should be under 'used_ingredients' and the ingredients that the user doesn't have should be under 'needed_ingredients'. Here is the example of your response format: {\"recipe\": "", \"user_ingredients\": "", \"needed_ingredients\", \"instructions\": ""}"}
                    ,{ "role": "user", "content": "How do I make moroccan meatballs when I have meatballs and oil"}
                    ,{ "role": "assistant", "content": "{\"recipe\": \"AlFez Moroccan Meatballs\",\"user_ingredients\": [\"Meatballs\",\"oil\"],\"needed_ingredients\": [\"AlFez  Moroccan Meatball Sauce\",\"Fresh coriander\",\"Cooked rice or couscous\"],\"instructions\":[\"1.\tIn a heated pan (or in the oven), brown the meatballs in oil, about 5 min.\"\r\n\"2.\tAdd the Al’FezTM Moroccan Meatball Sauce and simmer until the meatballs are cooked, about 20 min.\"\r\n\"3.\tServe over a be of rice or couscous. Garnish with fresh coriander.\"]}"}
                    ,{ "role": "user", "content": "How do I make make a meatball recipe for 4 people"}
                    ,{ "role": "assistant", "content": "{\"recipe\": \"AlFez Moroccan Meatballs\",\"needed_ingredients\": [\"12 Meatballs\",\"1 Tbsp Olive oil\",\"1 Jar AlFez  Moroccan Meatball Sauce\",\"Fresh coriander (for garnish)\",\"5 cups Cooked rice or couscous\"],\"instructions\":[\"1.\tIn a heated pan (or in the oven), brown the meatballs in oil, about 5 min.\"\r\n\"2.\tAdd the Al’FezTM Moroccan Meatball Sauce and simmer until the meatballs are cooked, about 20 min.\"\r\n\"3.\tServe over a be of rice or couscous. Garnish with fresh coriander.\"]}"}
                ]

        recipe_name = recipe_data.recipe_name
        serving_size = recipe_data.serving_size


        if(recipe_name and serving_size and recipe_ingredients):
            user_content = f"How do I make {recipe_name} for {serving_size} people when I have {recipe_ingredients}"
        elif (recipe_name and serving_size):
            user_content = f"How do I make {recipe_name} for {serving_size} people"
        elif (recipe_name and recipe_ingredients):
            user_content = f"How do I make {recipe_name} and I have {recipe_ingredients}"        
        elif (serving_size and recipe_ingredients):
            user_content = f"Please suggest a recipe that I can make using {recipe_ingredients} and I need to prepare meal for {serving_size} people"
        elif (recipe_name):
            user_content = f"How do I make {recipe_name}"
        elif (serving_size):
            user_content = f"How do I make a meal for {serving_size} people"
        else:
            user_content=f"Suggest a recipe that I can make using most of the following ingredients: {recipe_ingredients}"

        print (f"User content : {user_content}")
        user_prompt_message = { "role": "user", "content": user_content }
        messages.append(user_prompt_message)

        recipe_response = self.client1.chat.completions.create(
            model=self.deploymentid,
            messages=messages,
            # past_messages=10,        
            # temperature=0.5,
            extra_body={
                "data_sources": [
                    {
                        "type": "azure_search",
                        "parameters": {
                            "endpoint": os.environ["SEARCH_ENDPOINT"],
                            "index_name": os.environ["SEARCH_INDEX_NAME"],
                            "semantic_configuration": "azureml_default",
                            "authentication": {
                                "type": "api_key",
                                "key": os.environ["SEARCH_API_KEY"]
                            }                            
                        }
                    }
                ]
            }
        )

        print(f"recipe response is {recipe_response}")
        recipe_message = recipe_response.choices[0].message
        print(recipe_message)
        return recipe_message.content


if __name__ == "__main__":
    prompt_instance = Prompt()
    # Example usage
    response = prompt_instance.extractUserPrompt(
        "I am at Meijer store 21 and I have tomtoes, ground beef, and onions. I am thinking of making some Mediteranean dish."
    )
    print(response)