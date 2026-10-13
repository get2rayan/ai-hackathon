import os
import json
from langchain_core.messages import AIMessage, HumanMessage
import logging
from mlflow import prompt
from openai import OpenAI
import dotenv
from tdapp.core.state import UserRecipeIntent, WorkflowState
from langgraph.graph import MessagesState
from langchain_core.messages import convert_to_openai_messages

# try:
#     from .state import UserIntent
# except ImportError:
#     from state import UserIntent

dotenv.load_dotenv(override=True)


class PromptHandler():

    def __init__(self) -> None:

        self.aiclient = OpenAI()
        self.model = os.environ.get("DEPLOYMENT_NAME")

        # # # AI extension client to work with custom Meijer data
        # # self.client2 = openai.AzureOpenAI(
        # #     base_url=f"{self.endpoint}/openai/deployments/{self.deploymentid}/extensions",
        # #     api_key=self.api_key,
        # #     api_version="2024-08-01-preview"
        # # )

    def IsRecipeWarranted(self, messages_state: MessagesState) -> bool:
        user_message = messages_state['messages'][-1].content
        print(f"User prompt received: {user_message}")

        decision = self.aiclient.decisions.create(
            model=self.model,
            input = user_message,
            questions=[
                {
                    "type": "predicate",
                    "instructions": "Is the user looking for a recipe suggestion?"
                }
            ]
        )
        
        return True if decision.answers[0].probability > 0.5 else False


    def GenerateSimpleChatResponse(self, messages_state: MessagesState) -> MessagesState:
        # Placeholder for generating simple chat response
        chat_prompt = """
        You are a helpful recipe assistant who can suggest recipes based on user's needs. You will not assist the user other than recipe suggestions. 
        If the user is asking for anything other than recipes, politely decline and mention you can only assist with recipe suggestions.
        """
        return self._chat_and_append(messages_state, chat_prompt)
            

    def extractUserRecipeIntentFromMessages(self, messages_state: MessagesState) -> MessagesState:
        # Below user prompt can signify 
        # 1. a user adding items to cart where the recipe will be based on their cart items / user uses smart devices for managing their shopping list
        # 2. meijer specific products chosen based on criteria at the store like items in promotion / high inventory items at the (can be store specific).
        extraction_prompt = """
        You are a data extraction assistant. Your job is to extract information from the user input and return them STRICTLY as a valid JSON object.
        """
        response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "recipe_extraction",
                        "strict": True,
                        "schema": UserRecipeIntent.model_json_schema()
                    }
                }

        return self._chat_and_append(messages_state, extraction_prompt, response_format)
            
        
    def _chat_and_append(self, messages_state: MessagesState, system_prompt: str, response_format: dict | None = None) -> MessagesState:
        messages = [
            {"role": "system", "content": system_prompt},
            *convert_to_openai_messages(
                message for message in messages_state["messages"] if message.type == "human"
            )
        ]

        print(f"\nMessages sent to OpenAI: \n{messages}")

        options = {}
        if response_format is not None:
            options["response_format"] = response_format

        try:
            response = self.aiclient.chat.completions.create(
                model=self.model,
                messages=messages,
                **options
            )

            item_message = response.choices[0].message
            print(f"\nOpenAI response message: {item_message}")

            # convert the OpenAI response message to an AIMessage
            assistant_message = AIMessage(
                content=item_message.content,
                additional_kwargs={
                    "refusal": item_message.refusal,
                    "tool_calls": item_message.tool_calls,
                }
            )

            # Append the assistant message to the messages state and return the updated messages state
            messages_state['messages'] = [*messages_state['messages'], assistant_message]
            return messages_state

        except Exception as e:
            logging.exception(f"Exception in _chat_and_append : {e}")



if __name__ == "__main__":
    prompt_instance = PromptHandler()
    state={
            "messages_state": MessagesState(
                messages=[
                    # HumanMessage(content="I am at Meijer store 21 and I have tomatoes, ground beef, and onions. I am thinking of making some Mediteranean dish."),
                    HumanMessage(content="Give me an option without eggs"),
                ]
            )
        }
    # Example usage
    # response = prompt_instance.extractUserIntentFromWorkflowState(
    #     state={
    #         "messages_state": MessagesState(
    #             messages=[HumanMessage(content="I am at Meijer store 21 and I have tomatoes, ground beef, and onions. I am thinking of making some Mediteranean dish.")]
    #         )
    #     }
    # )
    response = prompt_instance.IsRecipeWarranted(messages_state=state["messages_state"])
    print(response)

    # recipes = prompt_instance.get_custom_recipes(response)
    # print(recipes)

# run this file as python3 -m tdapp.core.prompt_handler