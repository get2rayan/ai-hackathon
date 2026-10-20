from agents import Agent, AgentOutputSchema, Runner, function_tool, trace
import sys, os, dotenv
import mlflow
dotenv.load_dotenv(override=True)
from pathlib import Path
from tdapp.core.state import RecipeContext, UserRecipeIntent
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


# ── 1. MLflow setup ───────────────────────────────────────────
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("ai-hackathon")
mlflow.langchain.autolog()
mlflow.openai.autolog()

class RecipeHandler:
    def __init__(self) -> None:
        self.model = os.getenv("DEPLOYMENT_NAME")
        self.rag_handler = RAGHandler()
        pass

    
    def retrieve_recipe_context(self, query: str)->dict:
        """Retrieve relevant recipe context based on the user's query.

        Args:
            query (str): The user's query for recipe context.

        Returns:
            dict: Retrieved context from the RAG handler.
        """
        print(f"\nTOOL CALL: Retrieving recipe context for query: {query}")
        return self.rag_handler.retrieve_context(query)
    

    def get_promo_items(self, userRecipeIntent: UserRecipeIntent)->list:
            """
            Retrieve recipe items based on the user's intent.

            Args:
                userRecipeIntent (UserRecipeIntent): The user's recipe intent.

            Returns:
                list: A list of recipe items.
            """
            print(f"\nTOOL CALL: Retrieving recipe items for user intent: {userRecipeIntent}")
            # get user input from the workflow state
            if userRecipeIntent:
                store_id = userRecipeIntent.store_id
                category = userRecipeIntent.category
                user_ingredients = userRecipeIntent.user_ingredients
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


    async def get_custom_recipes(self, state: WorkflowState ) -> RecipeContext :
        """Generate custom recipes based on the current workflow state.

        Args:
            state (WorkflowState): The current state of the workflow containing user intent and recipe items.

        Returns:
            RecipeContext: Generated to be added to the workflow state.
        """
        # Todo: 
        # Extract user intent from the workflow state
        # pass the user intent to LLM to pull relevant recipes prioritized by recipe name, cuisine, ingredients
        # Parallelly, fetch relevant recipe from the web
        # Pass the combined recipe data to the next step in the workflow for evaluation
        # return item_message
        
        
        system_instruction = "You are a helpful recipe assistant. Use the tool retrieve_recipe_context \
            to get the context of relevant matching recipe. Base your recipe generation only on the retrieved context. \
            If no relevant recipe is available, return None. If metadata is provided, use the `id` property \
            as a bracket tag for citation. (e.g. [1] or [2])."

        userRecipeIntent: UserRecipeIntent = state.get('userRecipeIntent')
        
        if(userRecipeIntent):
            recipe_name = userRecipeIntent.recipe_name
            serving_size = userRecipeIntent.serving_size
            cuisine = userRecipeIntent.cuisine
        else:
            recipe_name = None
            serving_size = None
            cuisine = None

        recipe_ingredients = ', '.join(state.get('recipe_items', []))

        print(f"\nrecipe_name : {recipe_name} | cuisine: {cuisine} | recipe_ingredients: {recipe_ingredients} | serving_size: {serving_size}")
        if(recipe_name and serving_size and recipe_ingredients):
            user_prompt_message = f"User wants to make {recipe_name} for {serving_size} people and they have {recipe_ingredients}"
        elif (recipe_name and serving_size):
            user_prompt_message = f"User wants to make {recipe_name} for {serving_size} people"
        elif (recipe_name and recipe_ingredients):
            user_prompt_message = f"User wants to make {recipe_name} and they have {recipe_ingredients}"        
        elif (cuisine and recipe_ingredients):
            user_prompt_message = f"User wants to make {cuisine} dish and they have {recipe_ingredients}"
        elif (cuisine and serving_size):
            user_prompt_message = f"User wants to make {cuisine} dish for {serving_size} people"
        elif (serving_size and recipe_ingredients):
            user_prompt_message = f"User has {recipe_ingredients} and they need to prepare a dish for {serving_size} people"
        elif (recipe_name):
            user_prompt_message = f"User wants a recipe for {recipe_name}"
        elif (serving_size):
            user_prompt_message = f"User wants a recipe to make a dish for {serving_size} people"
        elif (cuisine):
            user_prompt_message = f"User wants a recipe to make {cuisine} dish"
        elif (recipe_ingredients):
            user_prompt_message=f"User wants a recipe that can be made using most of the following ingredients: {recipe_ingredients}"

        print (f"\nUser prompt message : {user_prompt_message}")
        
        with mlflow.start_run(run_name="recipe_agent_execution"):
            mlflow.set_tags({
                "agent_type": "recipe_agent",
                "llm_model": self.model,
                "framework": "openai"
            })
        # with trace('recipe_agent_execution'):
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
    user_intent: UserRecipeIntent = {
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
