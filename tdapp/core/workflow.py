import json

from langgraph.graph import START, StateGraph, END

from tdapp.core.recipe_handler import RecipeHandler
from tdapp.core.state import UserIntent

try:
    from .prompt_handler import PromptHandler
except ImportError:
    from prompt_handler import PromptHandler
from tdapp.core.state import WorkflowState


user_prompt:str = "I am at Meijer store 21 and I have tomatoes, ground beef, and onions. I am thinking of making some Mediteranean dish."


def get_user_intent(state: WorkflowState) -> dict:
    # Placeholder for extracting user intent from the state
    user_intent_json: UserIntent = PromptHandler().extractUserIntent(user_prompt)

    state['user_intent'] = user_intent_json
    print(f"State after extracting user intent: {state}")
    return state


def get_recipe_items(state: WorkflowState) -> dict:
    # Placeholder for generating recipe items based on user intent
    recipe_items = RecipeHandler().get_recipe_items(json.loads(state['user_intent']))

    state['recipe_items'] = recipe_items
    print(f"State after generating recipe items: {state}")
    return state


def get_recipes(state: WorkflowState) -> dict:
    # Placeholder for generating recipes based on recipe items
    recipes = RecipeHandler().get_recipes(json.loads(state['recipe_items']))

    state['recipes'] = recipes
    print(f"State after generating recipes: {state}")
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
    print(graph.get_graph().draw_mermaid())

    return graph



if __name__ == "__main__":
    workflow_graph = create_workflow_graph()
    print(workflow_graph)
    # Execute the workflow starting from the initial state
    initial_state= WorkflowState()
    final_state = workflow_graph.invoke(initial_state)
    print(f"Final state: {final_state}")