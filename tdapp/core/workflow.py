import json
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import START, MessagesState, StateGraph, END

from tdapp.core.recipe_handler import RecipeHandler
from tdapp.core.state import UserRecipeIntent

try:
    from .prompt_handler import PromptHandler
except ImportError:
    from prompt_handler import PromptHandler
from tdapp.core.state import WorkflowState


class Workflow():

    def __init__(self):
        self.prompt_handler = PromptHandler()
        self.recipe_handler = RecipeHandler()

    def check_user_intent(self, state: WorkflowState) -> dict:
        # Placeholder for checking user intent in the state
        is_recipe_needed = self.prompt_handler.IsRecipeWarranted(state['messages_state'])

        state['is_recipe_needed'] = is_recipe_needed
        return state


    def route_user_intent(self, state: WorkflowState) -> str:
        return "extract_user_recipe_intent" if state['is_recipe_needed'] else "generate_chat_response"
        

    def generate_chat_response(self, state: WorkflowState) -> dict:
        # Placeholder for extracting user intent from the state
        messages_state = self.prompt_handler.GenerateSimpleChatResponse(state['messages_state'])

        state['messages_state'] = messages_state
        print(f"\nState after generating chat response: {state}")
        return state


    def extract_user_recipe_intent(self, state: WorkflowState) -> dict:
        # Placeholder for extracting user intent from the state
        messages_state = self.prompt_handler.extractUserRecipeIntentFromMessages(state['messages_state'])

        state['messages_state'] = messages_state
        state['user_intent']= UserRecipeIntent.model_validate_json(messages_state['messages'][-1].content)
        print(f"\nState after extracting user intent: {state}")
        return state


    def get_recipe_items(self, state: WorkflowState) -> dict:
        # Placeholder for generating recipe items based on user intent
        recipe_items = self.recipe_handler.get_recipe_items(state['user_intent'])

        state['recipe_items'] = recipe_items
        print(f"\nState after generating recipe items: {state}")
        return state


    async def get_recipes(self, state: WorkflowState) -> dict:
        # Placeholder for generating recipes based on recipe items
        recipes = await self.recipe_handler.get_custom_recipes(state)

        state['recipe_context'] = recipes
        print(f"\nState after generating recipes: {state}")
        return state


    def create_workflow_graph(self):
        graph_builder = StateGraph(WorkflowState)

        graph_builder.add_node("check_user_intent", self.check_user_intent)
        graph_builder.add_node("generate_chat_response", self.generate_chat_response)
        graph_builder.add_node("extract_user_recipe_intent", self.extract_user_recipe_intent)
        graph_builder.add_node("get_recipe_items", self.get_recipe_items)
        graph_builder.add_node("get_recipes", self.get_recipes)

        graph_builder.add_edge(START, "check_user_intent")
        graph_builder.add_conditional_edges(
            "check_user_intent", 
            self.route_user_intent,
            {
                "extract_user_recipe_intent": 'extract_user_recipe_intent',
                "generate_chat_response": 'generate_chat_response'
            }
        )
        graph_builder.add_edge("extract_user_recipe_intent", END)
        graph_builder.add_edge("generate_chat_response", END)
        # graph_builder.add_edge("get_user_intent", "get_recipe_items")
        # graph_builder.add_edge("get_recipe_items", "get_recipes")
        # graph_builder.add_edge("get_recipes", END)
        
        graph = graph_builder.compile()

        #display the graph in mermaid format
        # print(graph.get_graph().draw_mermaid())

        return graph



def run_chat_workflow():
    import asyncio

    default_user_prompt:str = "I am at Meijer store 21 and I want to make biryani. I have only chicken and rice."
    chat_workflow = Workflow().create_workflow_graph()
    history: list[BaseMessage] = []

    initial_state= WorkflowState()
    initial_state = {
    "messages_state": {
        "messages": [HumanMessage(content=default_user_prompt)]
        }
    }
    result = asyncio.run(chat_workflow.ainvoke(initial_state))
    print(result)

    # print("\nRunning chat workflow...\n")


    # while True:
    #     try:
    #         user_input = input("You: ").strip()
    #     except KeyboardInterrupt:
    #         print("\nExiting chat workflow.")
    #         break

    #     if not user_input:
    #         user_input = default_user_prompt
        
    #     initial_state['messages_state']['messages'] = [*history, HumanMessage(content=user_input)]
        
    #     result = asyncio.run(chat_workflow.ainvoke(initial_state))
    #     history = result['messages_state']['messages']




if __name__ == "__main__":
    run_chat_workflow()