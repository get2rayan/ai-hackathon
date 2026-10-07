from agents import Agent, AgentOutputSchema, Runner, function_tool
import sys, os, dotenv
dotenv.load_dotenv(override=True)
from pathlib import Path
from tdapp.core.state import RecipeContext, UserIntent
from tdapp.core.rag_handler import RAGHandler
try:
    from .state import WorkflowState
except ImportError:
    from state import WorkflowState
try:
    from ..functions.store_products import store_products
except ImportError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from tdapp.functions.store_products import store_products


class RecipeHandler:
    def __init__(self) -> None:
        self.model = os.getenv("DEPLOYMENT_NAME")
        self.rag_handler = RAGHandler()
        pass

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

    
    def retrieve_recipe_context(self, query: str)->dict:
        """Retrieve relevant recipe context based on the user's query.

        Args:
            query (str): The user's query for recipe context.

        Returns:
            dict: Retrieved context from the RAG handler.
        """
        print(f"TOOL CALL: Retrieving recipe context for query: {query}")
        return self.rag_handler.retrieve_context(query)
    

    def get_recipe_items(self, user_intent: UserIntent)->list:
            # get user input from the workflow state
            if user_intent:
                store_id = user_intent.get('store_id')
                category = user_intent.get('category')
                user_ingredients = user_intent.get('user_ingredients')
            else:
                store_id = None
                category = None
                user_ingredients = None

            items_list = store_products().get_items_list(
                store_id=store_id,
                category=category,
                user_ingredients=user_ingredients
            )

            return items_list


    async def get_custom_recipes(self, state: WorkflowState ) -> dict :
            # Todo: 
            # Extract user intent from the workflow state
            # pass the user intent to LLM to pull relevant recipes prioritized by recipe name, cuisine, ingredients
            # Parallelly, fetch relevant recipe from the web
            # Pass the combined recipe data to the next step in the workflow for evaluation
            # return item_message
            
            
            system_instruction = "You are a helpful assistant that can suggest a best recipe as per user request."

            user_intent = state.get('user_intent')
            
            if(user_intent):
                recipe_name = user_intent.get('recipe_name')
                serving_size = user_intent.get('serving_size')
                cuisine = user_intent.get('cuisine')
            else:
                recipe_name = None
                serving_size = None
                cuisine = None

            recipe_ingredients = state.get('recipe_items')

            print(f"recipe_name : {recipe_name} - serving_size: {serving_size} - recipe_ingredients: {recipe_ingredients}")
            if(recipe_name and serving_size and recipe_ingredients):
                user_prompt_message = f"How do I make {recipe_name} for {serving_size} people when I have {recipe_ingredients}"
            elif (recipe_name and serving_size):
                user_prompt_message = f"How do I make {recipe_name} for {serving_size} people"
            elif (recipe_name and recipe_ingredients):
                user_prompt_message = f"How do I make {recipe_name} when I have {recipe_ingredients}"        
            elif (serving_size and recipe_ingredients):
                user_prompt_message = f"Suggest a recipe that I can make using {recipe_ingredients} and I need to prepare meal for {serving_size} people"
            elif (recipe_name):
                user_prompt_message = f"How do I make {recipe_name}"
            elif (serving_size):
                user_prompt_message = f"How do I make a meal for {serving_size} people"
            else:
                user_prompt_message=f"Suggest a recipe that can be made using the following ingredients: {recipe_ingredients}"

            print (f"User prompt message : {user_prompt_message}")
            

            recipe_agent = Agent(
                name="recipe_agent",
                instructions=system_instruction,
                model=self.model,
                tools=[function_tool(self.retrieve_recipe_context)],
                output_type=AgentOutputSchema(
                    RecipeContext, 
                    strict_json_schema=True
                )
            )

            recipe_response = await Runner.run(
                starting_agent=recipe_agent, 
                input=user_prompt_message
            )
                        
            return recipe_response.final_output
    


if __name__ == "__main__":
    recipe_handler = RecipeHandler()
    user_intent: UserIntent = {
        "store_id":21,
        "cuisine":"Mediterranean",
        "user_ingredients":["tomatoes","ground beef","onions"],
        "recipe_name":None,
        "serving_size":None,
        "category":["produce","meat"]
    }
    state: WorkflowState = {
        "user_intent": user_intent,
        "recipe_items": recipe_handler.get_recipe_items(user_intent),
    }
    # recipe_items = recipe_handler.get_recipe_items(user_intent)
    print(f"recipe_items: {state.get('recipe_items')}")

    import asyncio
    print(f"\nrecipe result: \n{asyncio.run(recipe_handler.get_custom_recipes(state))}")



    # state: WorkflowState = {'user_intent': {'store_id': 21, 'cuisine': 'Mediterranean', 'user_ingredients': ['tomatoes', 'ground beef', 'onions'], 'recipe_name': None, 'serving_size': None, 'category': ['produce', 'meat']}, 'recipe_items':['tomatoes', 'ground beef', 'onions', 'mango', 'apple', 'chicken', 'shrimp', 'avocado', 'fish', 'beef']}
