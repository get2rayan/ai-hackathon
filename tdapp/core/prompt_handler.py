import os
import json
import logging
from openai import OpenAI
import dotenv

try:
    from .user_params import UserIntent
except ImportError:
    from user_params import UserIntent

dotenv.load_dotenv(override=True)


class PromptHandler():

    def __init__(self) -> None:

        self.client1 = OpenAI()
        self.deploymentid = os.environ.get("DEPLOYMENT_NAME")
        
        # use_azure_active_directory = False  # Set this flag to True if you are using Azure Active Directory

        # if not use_azure_active_directory:
        #     self.endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        #     self.api_key = os.environ["AZURE_OPENAI_API_KEY"]
        #     # set the deployment model we want to use
        #     self.deploymentid =os.environ["DEPLOYMENT_NAME"]            
        
        # # Generic AI client to extract information from user prompt
        # self.client1 = OpenAI(
        #     base_url=self.endpoint,
        #     api_key=self.api_key,
        # )

        # print(f"Azure OpenAI client initialized with endpoint: {self.endpoint} and deployment: {self.deploymentid}")

        # # # AI extension client to work with custom Meijer data
        # # self.client2 = openai.AzureOpenAI(
        # #     base_url=f"{self.endpoint}/openai/deployments/{self.deploymentid}/extensions",
        # #     api_key=self.api_key,
        # #     api_version="2024-08-01-preview"
        # # )

    def extractUserIntent(self, userPrompt:str) -> str:
        print(f"User prompt received: {userPrompt}")

        # Below user prompt can signify 
        # 1. a user adding items to cart where the recipe will be based on their cart items / user uses smart devices for managing their shopping list
        # 2. meijer specific products chosen based on criteria at the store like items in promotion / high inventory items at the (can be store specific).
        system_prompt = """
        You are a data extraction assistant. Your job is to extract information from the user input and return them STRICTLY as a valid JSON object.
        """
        # If a category can be determined from the user input, use the available tool 'get_items_list' to fetch the items from the store.
        
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
                        "schema": UserIntent.model_json_schema()
                    }
                },
                # tools=self.tools,
                # tool_choice= "auto" #{"type": "function", "function": { "name": "get_store_products"} }
            )
            
            item_message = item_response.choices[0].message.content
            return item_message
        
            # if item_message.tool_calls is not None:
            #     return item_message.tool_calls[0].function.arguments
            # else:
            #     return item_message.content
            
        except Exception as e:
            logging.exception(f"Exception in extractUserPrompt : {e}")        



if __name__ == "__main__":
    prompt_instance = PromptHandler()
    # Example usage
    response = prompt_instance.extractUserIntent(
        userPrompt="I am at Meijer store 21 and I have tomatoes, ground beef, and onions. I am thinking of making some Mediteranean dish."
    )
    print(response)

    # recipes = prompt_instance.get_custom_recipes(response)
    # print(recipes)

# run this file as python3 -m tdapp.core.prompt_handler