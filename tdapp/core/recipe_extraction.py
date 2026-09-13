from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

# Define a reusable Literal type for clean code
StoreCategory = Literal["produce", "dairy", "bakery", "meat", "pantry", "frozen", "seafood"]


class RecipeExtraction(BaseModel):
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
