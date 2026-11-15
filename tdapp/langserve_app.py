import asyncio
import logging
import os
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import MessagesState
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from langserve import add_routes
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from pydantic import BaseModel, Field, field_validator

from tdapp.core.state import WorkflowState
from tdapp.core.workflow_service import format_workflow_reply, invoke_workflow_turn

load_dotenv()
logger = logging.getLogger(__name__)


class WorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    thread_id: str | None = None

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Please enter a message.")
        return value


class WorkflowResponse(BaseModel):
    reply: str
    thread_id: str


# Initialize Langfuse's OpenTelemetry provider before instrumenting Agents SDK runs.
langfuse_client = get_client()
OpenAIAgentsInstrumentor().instrument()


class WorkflowRunnable(Runnable[dict, dict]):
    def _prepare(self, input: dict) -> tuple[WorkflowRequest, dict]:
        request = WorkflowRequest.model_validate(input)
        # A browser conversation reuses its UUID; new or malformed IDs start a fresh thread.
        try:
            thread_id = str(UUID(request.thread_id or ""))
        except (TypeError, ValueError, AttributeError):
            thread_id = str(uuid4())
        return request, {
            "configurable": {"thread_id": thread_id},
            "callbacks": [CallbackHandler()],
        }

    async def _run(
        self,
        input: dict,
        stream_callback,
    ) -> dict:
        # Translate the public prompt payload into the LangGraph's internal state shape.
        request, workflow_config = self._prepare(input)
        workflow_state = WorkflowState()
        workflow_state["messages_state"] = MessagesState(
            messages=[HumanMessage(content=request.prompt)]
        )
        result = await invoke_workflow_turn(workflow_state, workflow_config, stream_callback)
        return {
            "reply": format_workflow_reply(result),
            "thread_id": workflow_config["configurable"]["thread_id"],
        }

    def invoke(
        self,
        input: dict,
        config: RunnableConfig | None = None,
        **kwargs,
    ) -> dict:
        return asyncio.run(self.ainvoke(input, config=config, **kwargs))

    async def ainvoke(
        self,
        input: dict,
        config: RunnableConfig | None = None,
        **kwargs,
    ) -> dict:
        return await self._run(input, lambda _event: None)

    async def astream(
        self,
        input: dict,
        config: RunnableConfig | None = None,
        **kwargs,
    ) -> AsyncIterator[dict]:
        queue: asyncio.Queue[dict | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        # Workflow callbacks may arrive outside this loop, so schedule SSE events thread-safely.
        def publish_event(event):
            if event is not None:
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "delta", "text": event})

        async def run_and_publish():
            try:
                reply = await self._run(input, publish_event)
                # Ensure queued final deltas are observed before the completed reply event.
                await asyncio.sleep(0)
                await queue.put({"type": "done", **reply})
            except Exception:
                logger.exception("Unable to process LangServe workflow request")
                await queue.put({
                    "type": "error",
                    "error": "Sorry, I couldn't process that message. Please try again.",
                })
            finally:
                await queue.put(None)

        task = asyncio.create_task(run_and_publish())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
            await task
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


workflow_runnable = WorkflowRunnable().with_types(
    input_type=WorkflowRequest,
    output_type=WorkflowResponse,
)

app = FastAPI(title="Store Recipe Assistant API")
frontend_origins = [
    origin.strip()
    for origin in os.environ.get(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5000,http://localhost:5000",
    ).split(",")
    if origin.strip()
]
# Allow the standalone browser app to call this API without opening it to arbitrary origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)
add_routes(app, workflow_runnable, path="/api/workflow")
