import os
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI
import dotenv
from tdapp.core.state import UserRecipeIntent, WorkflowState
from langgraph.graph import MessagesState
from langgraph.types import interrupt


# try:
#     from .state import UserIntent
# except ImportError:
#     from state import UserIntent

dotenv.load_dotenv(override=True)


class PromptHandler():

    def __init__(self) -> None:

        self.chatClient = ChatOpenAI(
            base_url=os.environ.get("OPENROUTER_BASE_URL"),
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            model="openai/gpt-6-luna"
        )
        self.structuredClient = self.chatClient.with_structured_output(schema=UserRecipeIntent)
        self.decisionClient = OpenAI()
        self.deployed_model = os.environ.get("DEPLOYMENT_NAME")

    
    def GetUserIntent(self, messages: list[BaseMessage]) -> dict:
        # get last user message
        user_message = next(
            msg.content
            for msg in reversed(messages)
            if isinstance(msg, HumanMessage)
        )
        print(f"User prompt received: {user_message}")

        decision = self.decisionClient.decisions.create(
            model=self.deployed_model,
            input = user_message,
            questions=[
                {
                    "type": "predicate",
                    "name": "is_recipe_needed",
                    "instructions": "Is the user looking for a new recipe suggestion?"
                },
                {
                    "type": "predicate",
                    "name": "is_human_agent_needed",
                    "instructions": "Is the user looking for a human agent assistance?"
                },
                {
                    "type": "choice",
                    "name": "emotional_level",
                    "instructions": "What is the user's emotional level?",
                    "choices": [
                        {"value": "Happy", "description": "The user is feeling happy."},
                        {"value": "Sad", "description": "The user is feeling sad."},
                        {"value": "Angry", "description": "The user is feeling angry."},
                        {"value": "Neutral", "description": "The user is feeling neutral."}
                    ]
                }
            ]
        )
        print(f"\nDecision: {decision.answers} for user message: '{user_message}'")
        return {
            "is_recipe_needed": True if decision.answers[0].probability > 0.6 else False,
            "is_human_agent_needed": True if decision.answers[1].probability > 0.5 else False,
            "emotional_level": decision.answers[2].choice if decision.answers[2].choice else "Neutral"
        }


    def handle_human_agent(self, messages: list[BaseMessage]) -> dict:
        # Placeholder for handling human agent requests        
        print(f"\nHandling human agent request: {messages[-1].content}")
        human_agent_response = interrupt(
            {
                "reason": "User requested human agent assistance.",
                "user_message": messages[-1].content
            }
        )

        return {"messages": [*messages, AIMessage(content=human_agent_response, response_metadata={"sender": "human_agent"})]}


    def handle_message(self, state: WorkflowState) -> WorkflowState:
        # Placeholder for handling user messages
        user_messages=[
            msg for msg in state['messages_state']['messages']
            if isinstance(msg, HumanMessage)
        ]
        print(f"\nUser messages: {user_messages}")
        if state['is_recipe_needed']:
            response = self.extractUserRecipeIntentFromMessages(user_messages)
            state['userRecipeIntent'] = response
            # state['userRecipeIntent'] = UserRecipeIntent.model_validate_json(response)
        else:
            response = self.generateSimpleChatResponse(user_messages)
            # Append the assistant message to the messages 
            state['messages_state']['messages'] = [*state['messages_state']['messages'], AIMessage(content=response.content)]

        print(f"\nAssistant response: {response}")
        return state


    def generateSimpleChatResponse(self, messages: list[BaseMessage]) -> BaseMessage:
        # Placeholder for generating simple chat response
        chat_prompt = "You are a helpful recipe assistant. Politely decline requests unrelated \
                        to recipes and briefly say you can help with recipe suggestions."
        return self.chatClient.invoke(
            input=[
                SystemMessage(content=chat_prompt),
                messages[-1]    # latest human message
            ]
        )
            

    def extractUserRecipeIntentFromMessages(self, messages: list[BaseMessage]):
        extraction_prompt = """
        You are a data extraction assistant who can assist with extracting structured recipe-related information from user's requests.
        Interpret the latest user request as the current request. Use earlier user requests only to resolve references or supply relevant
        recipe context. If the latest request changes or contradicts an earlier request, follow the latest request.
        """
        user_request_history = "\n".join([f"Request {i}: {msg.content}" for i, msg in enumerate(messages, start=1)])
        print(f"\nUser request history: \n{user_request_history}")

        return self.structuredClient.invoke(
            input=[
                SystemMessage(content=extraction_prompt),
                HumanMessage(content=user_request_history)
            ]
        )
        return self.chatClient.invoke(
            input=[
                SystemMessage(content=extraction_prompt),
                HumanMessage(content=user_request_history)
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "recipe_extraction",
                    "strict": True,
                    "schema": UserRecipeIntent.model_json_schema()
                }
            }
        )



if __name__ == "__main__":
    prompt_instance = PromptHandler()
    state={
            "messages_state": MessagesState(
                messages=[
                    # HumanMessage(content="I am at Store 21 and I have tomatoes, ground beef, and onions. I am thinking of making some Mediteranean dish."),
                    # HumanMessage(content="I like to play games"),
                    HumanMessage(content="I want to make an american dessert"),
                ]
            ),
            "is_recipe_needed": True
        }
    
    # Example usage for handle_message
    # --------------------------------
    response = prompt_instance.handle_message(
        state=state
    )
    print(f"\nHandle Message Response: {response}")


    # # Example usage to get Structured User Intent from prompt message
    #----------------------------------------------------------------
    response = prompt_instance.extractUserRecipeIntentFromMessages(
        messages=state["messages_state"]['messages']
    )
    print (f"\nExtracted User Recipe Intent: {response}")

    # # Example usage to get decisions AI response
    # #------------------------------------------
    # response = prompt_instance.IsRecipeWarranted(messages_state=state["messages_state"])
    # print(response)

    # Example usage to get custom recipes
    # -----------------------------------
    # recipes = prompt_instance.get_custom_recipes(response)
    # print(recipes)

# run this file as python3 -m tdapp.core.prompt_handler