from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState
from langgraph.types import Command

from tdapp.core.state import WorkflowState
from tdapp.core.workflow import Workflow, get_postgres_checkpointer


async def invoke_workflow_turn(workflow_state: WorkflowState, config: dict, stream_callback) -> dict:
    """Invoke one workflow turn, resuming human-agent interrupts as before."""
    try:
        checkpointer = await get_postgres_checkpointer()
        workflow = Workflow(
            stream_callback=stream_callback,
            checkpointer=checkpointer,
        ).create_workflow_graph()

        # Restore the saved thread and append only this turn's user message.
        incoming_messages = workflow_state["messages_state"]["messages"]
        latest_user_message = incoming_messages[-1]
        snapshot = await workflow.aget_state(config)
        saved_messages = snapshot.values.get("messages_state", {}).get("messages", [])
        messages = [*saved_messages, latest_user_message] if saved_messages else incoming_messages
        workflow_state["messages_state"] = MessagesState(messages=messages)

        result = await workflow.ainvoke(workflow_state, config=config)

        # Resume graph interrupts with the existing placeholder human-agent response.
        while True:
            snapshot = await workflow.aget_state(config)
            if not snapshot.next:
                break
            result = await workflow.ainvoke(
                Command(resume="A human agent will follow up with you shortly."),
                config=config,
            )

        # Store the user-facing reply so the next checkpointed turn sees the same history.
        reply = format_workflow_reply(result)
        messages = result.get("messages_state", {}).get("messages", [])
        if not messages or not isinstance(messages[-1], AIMessage) or messages[-1].content != reply:
            messages = [*messages, AIMessage(content=reply)]
            result["messages_state"] = MessagesState(messages=messages)
            await workflow.aupdate_state(config, {"messages_state": MessagesState(messages=messages)})
        return result
    finally:
        stream_callback(None)


def format_workflow_reply(result: dict) -> str:
    """Convert workflow output into readable assistant reply text."""
    recipe_context = result.get("recipe_context")
    if result.get("is_recipe_needed"):
        if isinstance(recipe_context, str):
            return recipe_context
        recipes = getattr(recipe_context, "recipes", []) if recipe_context else []
        if recipes:
            return "\n\n".join(_format_recipe(recipe) for recipe in recipes)

    messages = result.get("messages_state", {}).get("messages", [])
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return str(message.content)

    if result.get("is_human_agent_needed"):
        return "Your request for a human representative has been received."
    return "I couldn't find a response for that message. Please try again."


def _format_recipe(recipe) -> str:
    lines = [recipe.name]
    if recipe.cuisine:
        lines.append(f"Cuisine: {recipe.cuisine}")
    if recipe.prep_time:
        lines.append(f"Prep time: {recipe.prep_time} minutes")
    if recipe.ingredients:
        lines.extend(["", "Ingredients:", *(f"- {item}" for item in recipe.ingredients)])
    if recipe.instructions:
        lines.extend(["", "Instructions:", recipe.instructions])
    if recipe.citation:
        lines.extend(["", f"Source: {recipe.citation}"])
    return "\n".join(lines)
