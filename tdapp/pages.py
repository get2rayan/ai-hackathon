import asyncio
import threading
from uuid import uuid4

from flask import Blueprint, current_app, flash, jsonify, render_template, request
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState
from langgraph.types import Command

from tdapp.core.state import WorkflowState
from tdapp.core.workflow import Workflow

bp=Blueprint("pages", __name__)
_workflow_loop = None
_workflow_loop_lock = threading.Lock()


@bp.route("/", methods=('GET', 'POST'))
def home():    
    """Render the home page and handle the legacy form submission."""

    if request.method=='POST':
        userprompt = request.form['userPrompt'].strip()
        if not userprompt:            
            flash('Please enter a valid user prompt')
            return render_template("pages/home.html")
        else: 
            workflow = Workflow()
            workflow_state = WorkflowState()
            workflow_state['messages_state'] = MessagesState(messages=[HumanMessage(content=userprompt)])
            wg = workflow.create_workflow_graph()
            # try:
            response = wg.invoke(workflow_state)
            # except Exception as e:
            #     flash('An error occurred while processing your request : \n' + str(e))
            #     return render_template("pages/home.html")

            # messages = {
            #     "content":{
            #         'extract_args': extract_resp.tool_calls[0].function.arguments,
            #         'recipe_resp':recipe_resp
            #     }
            # }
            return render_template("pages/home.html", extract_args= "" , recipe_resp=response)
    
    return render_template("pages/home.html")


@bp.post("/chat")
def chat():
    """Run a chat turn and return the assistant response as JSON."""
    payload = request.get_json(silent=True) or {}
    user_prompt = payload.get("prompt", "").strip()
    if not user_prompt:
        return jsonify(error="Please enter a message."), 400
    
    print(f"\nUser prompt: {user_prompt}")

    messages = []
    for item in payload.get("messages", [])[-20:]:
        if not isinstance(item, dict) or not isinstance(item.get("content"), str):
            continue
        if item.get("role") == "user":
            messages.append(HumanMessage(content=item["content"]))
        elif item.get("role") == "assistant":
            messages.append(AIMessage(content=item["content"]))
    messages.append(HumanMessage(content=user_prompt))

    print(f"\nMessages: {messages}")

    try:
        workflow_state = WorkflowState()
        workflow_state["messages_state"] = MessagesState(messages=messages)
        config = {"configurable": {"thread_id": str(uuid4())}}
        loop = _get_workflow_loop()
        result = asyncio.run_coroutine_threadsafe(
            _invoke_workflow(workflow_state, config), loop
        ).result()
        print(f"\nResult: {result}")
        reply = _format_workflow_reply(result)        
        return jsonify(reply=reply)
    except Exception:
        current_app.logger.exception("Unable to process chat message")
        return jsonify(error="Sorry, I couldn't process that message. Please try again."), 500


def _get_workflow_loop():
    """Return the shared background event loop used for async workflows."""
    global _workflow_loop
    with _workflow_loop_lock:
        if _workflow_loop is None or _workflow_loop.is_closed():
            _workflow_loop = asyncio.new_event_loop()
            loop_thread = threading.Thread(
                target=_workflow_loop.run_forever,
                name="workflow-event-loop",
                daemon=True,
            )
            loop_thread.start()
    return _workflow_loop


async def _invoke_workflow(workflow_state: WorkflowState, config: dict) -> dict:
    """Invoke the workflow and resume any human-agent interrupt."""
    workflow = Workflow().create_workflow_graph()
    result = await workflow.ainvoke(workflow_state, config=config)

    while True:
        snapshot = await workflow.aget_state(config)
        if not snapshot.next:
            return result

        result = await workflow.ainvoke(
            Command(resume="A human agent will follow up with you shortly."),
            config=config,
        )


def _format_workflow_reply(result: dict) -> str:
    """Convert workflow output into readable assistant reply text."""
    recipe_context = result.get("recipe_context")
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
    """Format one structured recipe as plain text for the chat response."""
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


@bp.route("/about")
def about():
    """Render the about page."""
    return render_template("pages/about.html")