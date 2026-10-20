from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import START, MessagesState, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from tdapp.core.recipe_handler import RecipeHandler
from tdapp.core.state import UserRecipeIntent

try:
    from .prompt_handler import PromptHandler
except ImportError:
    from prompt_handler import PromptHandler
from tdapp.core.state import WorkflowState

from langchain_core.globals import set_llm_cache
from langchain_redis import RedisSemanticCache

REDIS_URL = "redis://localhost:6379"
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
memory = MemorySaver()


# # Initialize the Redis semantic cache
# set_llm_cache(
#     RedisSemanticCache(
#         redis_url=REDIS_URL,
#         embeddings = embeddings,
#         distance_threshold = 0.2,
#         ttl=3600
#     )
# )


class Workflow():

    def __init__(self):
        self.prompt_handler = PromptHandler()
        self.recipe_handler = RecipeHandler()


    def check_user_intent(self, state: WorkflowState) -> dict:
        # Placeholder for checking user intent in the state
        is_recipe_needed = self.prompt_handler.IsRecipeWarranted(state['messages_state']['messages'])
        state['is_recipe_needed'] = is_recipe_needed
        return state


    def handle_user_message(self, state: WorkflowState) -> dict:
        # Placeholder for handling user messages
        state = self.prompt_handler.handle_message(state)
        return state


    def route_recipe_intent(self, state: WorkflowState) -> str:
        return "get_promo_items" if state['is_recipe_needed'] else "end"

    
    def get_promo_items(self, state: WorkflowState) -> dict:
        # Placeholder for generating recipe items based on user intent
        recipe_items = self.recipe_handler.get_promo_items(state['userRecipeIntent'])
        state['recipe_items'] = recipe_items
        # print(f"\nState after generating recipe items: {state}")
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
        graph_builder.add_node("handle_user_message", self.handle_user_message)
        graph_builder.add_node("get_promo_items", self.get_promo_items)
        graph_builder.add_node("get_recipes", self.get_recipes)

        graph_builder.add_edge(START, "check_user_intent")
        graph_builder.add_edge("check_user_intent", "handle_user_message")
        graph_builder.add_conditional_edges(
            "handle_user_message", 
            self.route_recipe_intent,
            {
                "get_promo_items": 'get_promo_items',
                "end": END
            }
        )
        graph_builder.add_edge("get_promo_items", "get_recipes")
        graph_builder.add_edge("get_recipes", END)
        
        graph = graph_builder.compile(checkpointer=memory)

        #display the graph in mermaid format
        # print(graph.get_graph().draw_mermaid())

        return graph



async def _run_chat_workflow():
    
    # default_user_prompt:str = "I am at Meijer store 21 and I want to make biryani. I have chicken and rice."
    default_user_prompt:str = "I want to make biryani. I have chicken and rice."
    chat_workflow = Workflow().create_workflow_graph()
    history: list[BaseMessage] = []

    initial_state= WorkflowState()
    initial_state["messages_state"]={
            "messages": [HumanMessage(content=default_user_prompt)]
        }

    # # result = asyncio.run(chat_workflow.ainvoke(initial_state))
    # print(result)

    print("\nRunning chat workflow...\n")
    current_state = initial_state

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat workflow.")
            break

        if not user_input:
            user_input = default_user_prompt
        
        config = {"configurable": {"thread_id": str(uuid4())}}
        current_state['messages_state']['messages'] = [*history, HumanMessage(content=user_input)]
        
        result = await chat_workflow.ainvoke(current_state, config=config)
        history = result['messages_state']['messages']




if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_chat_workflow())