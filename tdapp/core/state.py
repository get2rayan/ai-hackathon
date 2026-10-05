from typing import List, Dict, TypedDict
from pydantic import Field
from tdapp.core.user_params import UserIntent



class EvaluatorOutput(TypedDict):
    feedback: str=Field(description="Feedback from the evaluator on the generated recipe content")
    evaluation_scores: Dict[str, float]
    success_criteria_met: bool=Field(description="Indicates whether the generated recipe content meets the success criteria")
    overall_score: float=Field(description="Overall score for the generated recipe content based on evaluation metrics")



class WorkflowState(TypedDict):
    user_intent: UserIntent=Field(description="The intent of the user based on their input")
    recipe_items: List[str]=Field(description="List of recipe items generated based on user intent")
    evaluator_output: EvaluatorOutput



