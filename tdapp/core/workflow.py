from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import START, MessagesState, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
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
        user_intent = self.prompt_handler.GetUserIntent(state['messages_state']['messages'])
        state['is_recipe_needed'] = user_intent['is_recipe_needed']
        # state['emotional_level'] = user_intent['emotional_level']
        state['is_human_agent_needed'] = user_intent['is_human_agent_needed']
        return state


    def route_user_intent(self, state: WorkflowState) -> str:
        if state['is_human_agent_needed']:
            return "handle_human_agent"
        else:
            return "handle_user_message"
    
    
    def handle_human_agent(self, state: WorkflowState) -> dict:
        # Placeholder for handling human agent requests
        human_agent_state = self.prompt_handler.handle_human_agent(state['messages_state']['messages'])
        # handle_human_agent returns {"messages": [...]} after the interrupt resumes
        state['messages_state'] = human_agent_state
        # unset flag for human agent
        state["is_human_agent_needed"] = False
        print(f"\nMessage State after handling human agent request: {state['messages_state']['messages']}")
        return state


    def handle_user_message(self, state: WorkflowState) -> dict:
        # Placeholder for handling user messages
        state = self.prompt_handler.handle_message(state)
        return state

    
    def route_recipe_intent(self, state: WorkflowState) -> str:
        return "get_promo_items" if state['is_recipe_needed'] else END

    
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
        graph_builder.add_node("handle_human_agent", self.handle_human_agent)
        graph_builder.add_node("handle_user_message", self.handle_user_message)
        graph_builder.add_node("get_promo_items", self.get_promo_items)
        graph_builder.add_node("get_recipes", self.get_recipes)

        graph_builder.add_edge(START, "check_user_intent")
        graph_builder.add_conditional_edges(
            "check_user_intent",
            self.route_user_intent,
            {
                "handle_human_agent": "handle_human_agent",
                "handle_user_message": "handle_user_message"
            }
        )
        graph_builder.add_edge("handle_human_agent", END)
        graph_builder.add_conditional_edges(
            "handle_user_message", 
            self.route_recipe_intent            
        )
        graph_builder.add_edge("get_promo_items", "get_recipes")
        graph_builder.add_edge("get_recipes", END)
        
        graph = graph_builder.compile(checkpointer=memory)

        #display the graph in mermaid format
        # print(graph.get_graph().draw_mermaid())

        return graph



async def _run_chat_workflow():
    # from IPython import display, Image
    # default_user_prompt:str = "I am at Meijer store 21 and I want to make biryani. I have chicken and rice."
    # default_user_prompt:str = "I want to make biryani. I have chicken and rice."
    default_user_prompt:str = "I want to get to a representative. I am not happy."
    chat_workflow = Workflow().create_workflow_graph()
    
    # display graph
    # display(Image(chat_workflow.get_graph().draw_mermaid_png()))

    history: list[BaseMessage] = []

    initial_state= WorkflowState()
    initial_state["messages_state"]={
            "messages": [HumanMessage(content=default_user_prompt)]
        }

    # # result = asyncio.run(chat_workflow.ainvoke(initial_state))
    # print(result)

    print("\nRunning chat workflow...\n")
    current_state = initial_state
    
    config = {"configurable": {"thread_id": str(uuid4())}}
        
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat workflow.")
            break

        if not user_input:
            user_input = default_user_prompt
        
        current_state['messages_state']['messages'] = [*history, HumanMessage(content=user_input)]

        result = await chat_workflow.ainvoke(current_state, config=config)

        # If the graph was interrupted waiting for a human agent, resume it
        # with the agent's response once it is available.
        while True:
            snapshot = await chat_workflow.aget_state(config)
            print(f"Current workflow state: {snapshot}")
            if snapshot.next:  # graph is paused at an interrupted node
                agent_response = input("\nHuman agent: ").strip()
                if not agent_response:
                    agent_response = "An agent will follow up with you shortly."
                result = await chat_workflow.ainvoke(
                    Command(resume=agent_response), config=config
                )
            else:
                break

        history = result['messages_state']['messages']




if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_chat_workflow())