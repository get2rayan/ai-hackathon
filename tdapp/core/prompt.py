import os
import openai
import dotenv
import logging
from ..functions import recipes
import json

class Prompt():

    def __init__(self) -> None:        
        dotenv.load_dotenv()

        use_azure_active_directory = False  # Set this flag to True if you are using Azure Active Directory

        if not use_azure_active_directory:
            self.endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
            self.api_key = os.environ["AZURE_OPENAI_API_KEY"]
            # set the deployment model we want to use
            self.deploymentid = "gpt-4o"
            # self.deploymentid = "gpt35turbo16k"
        
        # Generic AI client to extract information from user prompt
        self.client1 = openai.AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version="2024-08-01-preview"    #2023-09-01-preview
        )

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
                        "name": "get_items_for_recipe",
                        "description": "Get the recipe information based on user input requirement and meijer store product",
                        "parameters": {
                            "type":"object",
                            "properties": {
                                "storeid": {
                                    "type": "integer",
                                    "description": "The store id of Meijer store if specified, eg: 21 for Alpine",
                                },
                                "user_ingredients": {
                                    "type": "string",
                                    "description": f"""
                                            Comma separated list of ingredients for the recipe extracted from user's input.
                                            """
                                },
                                "recipe_name":{
                                    "type": "string",
                                    "description":"name of the recipe if specified."
                                },
                                "serving_size": {
                                    "type": "integer",
                                    "description": "The serving size or the portion size based on number of people, eg: 4 for 4 people",
                                }
                            },
                            "required": [],
                        }
                    }
                }
            ]
        )
    
    def extractUserPrompt(self, userPrompt:str) -> str:
         
        # Below user prompt can signify 
        # 1. a user adding items to cart where the recipe will be based on their cart items / user uses smart devices for managing their shopping list
        # 2. meijer specific products chosen based on criteria at the store like items in promotion / high inventory items at the (can be store specific).
        system_message = [{ "role": "system", "content": "You are an AI assistant that can extract store info, names of ingredients, recipe name, serving size from the user prompt as a JSON object. Do not assume storeid or ingredients if not specified explicitly." }]
        user_messages = [ 
                        {"role": "user", "content": "I am at Meijer store 21 and have banana and milk in my cart"}, {"role": "assistant", "content": "{\"storeid\": 21, \"user_ingredients\": \"banana, milk\"}"}
                        ,{"role": "user", "content": "I am planning to make chicken fajitas"}, {"role": "assistant", "content": "{\"recipe_name\": \"chicken fajitas\"}"}
                        ,{"role": "user", "content": "I want to make shrimp scampi but only have shrimp and butter. What else do I need?"}, {"role": "assistant", "content": "{\"recipe_name\": \"shrimp scampi\", user_ingredients=\"shrimp, butter\"}"}
                        ,{"role": "user", "content": "I am at a Meijer store and wondering what I can make with avocado and egg"}, {"role": "assistant", "content": "{\"user_ingredients\": \"avocado, egg\"}"}
                        ,{"role": "user", "content": "What do I need to make an Indian dessert?"}, {"role": "assistant", "content": "{\"recipe_name\": \"Vermicelli Kheer\"}"}
                        ,{"role": "user", "content": "I want to cook something for 6 people. What are my options"}, {"role": "assistant", "content": "{\"serving_size\": 6}"}
                        ,{"role": "user", "content": "I want to know what items are in Meijer store to make soup"}, {"role": "assistant", "content": "{\"recipe_name\": \"soup\"}"}
                        ,{"role": "user", "content": "I am looking for a meatball recipe?"}, {"role": "assistant", "content": "{\"recipe_name\": \"meatball\"}"}
                        ,{"role": "user", "content": "What can I make with meatball for 4 people?"}, {"role": "assistant", "content": "{\"user_ingredient\": \"meatball\", \"serving_size\": 4}"}
                        ,{"role": "user", "content": "What are some soup options to make"}, {"role": "assistant", "content": "{\"recipe_name\": \"soup\"}"}
                        ,{"role": "user", "content": "What are some ingredients for making a dessert"}, {"role": "assistant", "content": "{\"recipe_name\": \"dessert\"}"}
                    ]
        
        user_prompt_message = [{ "role": "user", "content": userPrompt }]
        # messages = [system_message, user_messages, user_prompt_message]
        messages = system_message + user_messages + user_prompt_message
            
        try: 
            item_response = self.client1.chat.completions.create(
                model=self.deploymentid,
                messages=messages,    
                tools=self.tools,
                tool_choice= "auto" #{"type": "function", "function": { "name": "get_items_for_recipe"} }
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
        recipe_ingredients =None
        # print(f'item_message: {item_message}')
        # check if the model wanted to call a function
        if dict(item_message).get('tool_calls'):
            available_functions = {
                "get_items_for_recipe": recipes.recipes().get_items_for_recipe
            }
            
            # extracting the functions
            for tool_call in item_message.tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)

                storeid = function_args.get('storeid')
                recipe_name = function_args.get('recipe_name')
                serving_size = function_args.get('serving_size')
                user_ingredients=function_args.get('user_ingredients')

                function_resp = function_to_call(
                    storeid=storeid
                    ,user_ingredients=user_ingredients
                )
                print(f"function_args : {function_args} - storeid :{function_args.get('storeid')}  - user_ingredients: {function_args.get('user_ingredients')} - recipe_name: {function_args.get('recipe_name')} - serving_size: {function_args.get('serving_size')}")
                recipe_ingredients=function_resp    
        else:
            recipe_ingredients=recipes.recipes().get_items_for_recipe()

        print(f"recipe_ingredients : {recipe_ingredients}")

        messages=[
                    { "role": "system", "content": "You are an AI assistant that can suggest one recipe based on either the ingredients specified by the user and / or recipe name and / or serving size. Return recipe name, ingredients and instructions of the recipe in a json format. The ingredients that the user has should be under 'used_ingredients' and the ingredients that the user doesn't have should be under 'needed_ingredients'. Here is the example of your response format: {\"recipe\": "", \"user_ingredients\": "", \"needed_ingredients\", \"instructions\": ""}"}
                    ,{ "role": "user", "content": "How do I make moroccan meatballs when I have meatballs and oil"}
                    ,{ "role": "assistant", "content": "{\"recipe\": \"AlFez Moroccan Meatballs\",\"user_ingredients\": [\"Meatballs\",\"oil\"],\"needed_ingredients\": [\"AlFez  Moroccan Meatball Sauce\",\"Fresh coriander\",\"Cooked rice or couscous\"],\"instructions\":[\"1.\tIn a heated pan (or in the oven), brown the meatballs in oil, about 5 min.\"\r\n\"2.\tAdd the Al’FezTM Moroccan Meatball Sauce and simmer until the meatballs are cooked, about 20 min.\"\r\n\"3.\tServe over a be of rice or couscous. Garnish with fresh coriander.\"]}"}
                    ,{ "role": "user", "content": "How do I make make a meatball recipe for 4 people"}
                    ,{ "role": "assistant", "content": "{\"recipe\": \"AlFez Moroccan Meatballs\",\"needed_ingredients\": [\"12 Meatballs\",\"1 Tbsp Olive oil\",\"1 Jar AlFez  Moroccan Meatball Sauce\",\"Fresh coriander (for garnish)\",\"5 cups Cooked rice or couscous\"],\"instructions\":[\"1.\tIn a heated pan (or in the oven), brown the meatballs in oil, about 5 min.\"\r\n\"2.\tAdd the Al’FezTM Moroccan Meatball Sauce and simmer until the meatballs are cooked, about 20 min.\"\r\n\"3.\tServe over a be of rice or couscous. Garnish with fresh coriander.\"]}"}
                ]
            
        if(recipe_name and serving_size and user_ingredients):
            user_content = f"How do I make {recipe_name} for {serving_size} people when I have {user_ingredients}"
        elif (recipe_name and serving_size):
            user_content = f"How do I make {recipe_name} for {serving_size} people"
        elif (recipe_name and user_ingredients):
            user_content = f"How do I make {recipe_name} and I have {user_ingredients}"        
        elif (serving_size and user_ingredients):
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
