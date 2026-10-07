from typing import List, Dict, TypedDict
from pydantic import Field
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

# Define a reusable Literal type for clean code
StoreCategory = Literal["produce", "dairy", "bakery", "meat", "pantry", "frozen", "seafood"]
RecipeCategory = Literal['store', 'web']

class UserIntent(BaseModel):
    model_config = ConfigDict(extra='forbid')

    store_id: Optional[int] = Field(..., description="Id of the grocery store or supermarket.")
    cuisine: Optional[str] = Field(..., description="The regional or cultural style of the cooking (e.g., Italian, Mexican).")
    user_ingredients: Optional[List[str]] = Field(..., description="List of ingredients explicitly mentioned as available.")
    recipe_name: Optional[str] = Field(..., description="The specific name of the dish or recipe.")
    serving_size: Optional[int] = Field(..., description="The number of people the recipe serves or portion size.")
    category: List[StoreCategory] = Field(
        ..., 
        description=(
            "A list of all store departments or categories relevant to the items needed to recommend a recipe based on user's requirement. "
            "For example, banana bread would return ['produce', 'bakery', 'dairy']. "
            "Return an empty list [] if no categories can be determined from the prompt."
        )
    )


class EvaluatorOutput(TypedDict):
    feedback: str=Field(description="Feedback from the evaluator on the generated recipe content")
    evaluation_scores: Dict[str, float]
    success_criteria_met: bool=Field(description="Indicates whether the generated recipe content meets the success criteria")
    overall_score: float=Field(description="Overall score for the generated recipe content based on evaluation metrics")


class Recipe(TypedDict):
    name: str=Field(description="Name of the recipe")
    cuisine: str=Field(description="Cuisine type of the recipe")
    ingredients: List[str]=Field(description="List of ingredients required for the recipe")
    instructions: str=Field(description="Instructions to prepare the recipe")
    nutrition: Optional[Dict[str, float]]=Field(description="Nutritional information for the recipe, e.g., calories, protein, fat")
    prep_time: int=Field(description="Preparation time for the recipe in minutes")
    category: RecipeCategory=Field(description="Category of the recipe, either 'store' or 'web'")


class Context(TypedDict):
    retrieved_data: Dict[str, str]=Field(description="Data retrieved from the RAG handler based on the user query")


class RecipeContext(TypedDict):
    context: Context=Field(description="Contextual information retrieved from the RAG handler")
    recipes: List[Recipe]=Field(description="List of recipes generated based on the context")


class WorkflowState(TypedDict):
    user_intent: UserIntent=Field(description="The intent of the user based on their input")
    recipe_items: List[str]=Field(description="List of recipe items generated based on user intent and shrinkage adjustments")
    recipe_context: RecipeContext=Field(description="Contextual information and store recipes related to the current workflow")
    evaluator_output: EvaluatorOutput=Field(description="Output from the evaluator including feedback and scores")



