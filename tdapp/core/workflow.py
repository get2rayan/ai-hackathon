import json

from langgraph.graph import START, StateGraph, END

from tdapp.core.recipe_handler import RecipeHandler
from tdapp.core.state import UserIntent

try:
    from .prompt_handler import PromptHandler
except ImportError:
    from prompt_handler import PromptHandler
from tdapp.core.state import WorkflowState


user_prompt:str = "I am at Meijer store 21 and I want to make biryani. I have only chicken and rice."


def get_user_intent(state: WorkflowState) -> dict:
    # Placeholder for extracting user intent from the state
    user_intent_json: UserIntent = PromptHandler().extractUserIntent(user_prompt)

    state['user_intent'] = user_intent_json
    print(f"\nState after extracting user intent: {state}")
    return state


def get_recipe_items(state: WorkflowState) -> dict:
    # Placeholder for generating recipe items based on user intent
    recipe_items = RecipeHandler().get_recipe_items(state['user_intent'])

    state['recipe_items'] = recipe_items
    print(f"\nState after generating recipe items: {state}")
    return state


async def get_recipes(state: WorkflowState) -> dict:
    # Placeholder for generating recipes based on recipe items
    recipes = await RecipeHandler().get_custom_recipes(state)

    state['recipe_context'] = recipes
    print(f"\nState after generating recipes: {state}")
    return state


def create_workflow_graph():
    graph_builder = StateGraph(WorkflowState)

    graph_builder.add_node("get_user_intent", get_user_intent)
    graph_builder.add_node("get_recipe_items", get_recipe_items)
    graph_builder.add_node("get_recipes", get_recipes)

    graph_builder.add_edge(START, "get_user_intent")
    graph_builder.add_edge("get_user_intent", "get_recipe_items")
    graph_builder.add_edge("get_recipe_items", "get_recipes")
    graph_builder.add_edge("get_recipes", END)
    
    graph = graph_builder.compile()

    #display the graph in mermaid format
    # print(graph.get_graph().draw_mermaid())

    return graph


import asyncio

if __name__ == "__main__":
    workflow_graph = create_workflow_graph()
    print(workflow_graph)
    # Execute the workflow starting from the initial state
    initial_state= WorkflowState()
    final_state = asyncio.run(workflow_graph.ainvoke(initial_state))
    print(f"\nFinal state: {final_state}")