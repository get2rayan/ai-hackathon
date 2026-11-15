# AI Store Recipe Assistant

A Store recipe assistant prototype with a browser-based chat interface. It extracts recipe intent, looks up store products, and generates recipe suggestions using retrieval-augmented generation (RAG) over a local recipe dataset.

## Application flow

The Flask frontend and LangServe workflow API run as separate services. The browser sends each chat turn directly to the LangServe endpoint in `tdapp/langserve_app.py`, which invokes the LangGraph workflow in `tdapp/core/workflow.py`:

1. `PromptHandler` identifies whether the request is recipe-related or asks for human-agent assistance, and extracts structured recipe intent using the `UserRecipeIntent` schema.
2. `RecipeHandler` requests store products through `store_products`. Product lookup uses MySQL filters for store and department; user-provided ingredients are prioritized and the combined list is capped at 10 items.
3. For recipe requests, the agent builds a recipe query from the extracted intent and available ingredients, then can retrieve relevant context from the FAISS index. The current RAG lookup returns one matching recipe document.
4. The API formats the workflow result and returns it to the browser.

The chat page stores up to 50 displayed messages in browser `localStorage`. A stable conversation ID is sent with each request so the workflow can restore state from PostgreSQL. Use **Clear chat** to remove the saved transcript and start a new conversation. Human-agent requests currently resume with a placeholder message that a representative will follow up; no live human-agent service is connected.

LangGraph checkpoints are stored in PostgreSQL. The browser keeps a stable conversation ID, which is used as the checkpoint `thread_id`, so checkpointed workflow state can be restored across requests and application restarts. The checkpoint tables are created automatically the first time the app connects.

`RAGHandler` uses OpenAI `text-embedding-3-small` embeddings over `tdapp/data/recipes_dataset.json`. If `faiss_index/index.faiss` is missing, the index is built from the recipe data and saved locally. This requires a working OpenAI API key.

## Requirements

- Python 3.13 or newer
- `uv`
- An OpenAI API key for intent decisions and embeddings
- An OpenRouter API key and base URL for chat-model requests
- A `DEPLOYMENT_NAME` accepted by the configured model providers
- MySQL and a database containing the `store_items` table for store-product lookups
- PostgreSQL for persistent LangGraph checkpoints

## Setup

Install dependencies from the repository root:

```bash
uv sync
```

Create a `.env` file in the repository root. Keep credentials private and do not commit this file:

```dotenv
OPENAI_API_KEY=your-openai-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
DEPLOYMENT_NAME=your-model-name
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_BASE_URL=https://cloud.langfuse.com

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=your-database-name

LANGGRAPH_POSTGRES_URI=postgresql://postgres:your-password@localhost:5432/ai_hackathon

```

For the separate web services, set these additional `.env` values (also shown in `.env.template`):

```dotenv
FLASK_RUN_PORT=5000
LANGSERVE_URL=http://127.0.0.1:8000
FRONTEND_ORIGINS=http://127.0.0.1:5000,http://localhost:5000
```

`LANGSERVE_URL` configures the API URL used by the Flask page, while `FRONTEND_ORIGINS` is the comma-separated list of browser origins allowed by the API. Change both for your deployment as needed.

The OpenAI key is used by the OpenAI client and embeddings; the OpenRouter values configure `ChatOpenAI`. The selected `DEPLOYMENT_NAME` must be available for the configured model calls. Langfuse credentials enable workflow, direct intent-decision, and OpenAI Agents SDK tracing. Use your region's base URL or your self-hosted URL in `LANGFUSE_BASE_URL`.

Create the PostgreSQL database named in `LANGGRAPH_POSTGRES_URI` before starting the app. The connection user needs permission to create the LangGraph checkpoint tables. URL-encode special characters in the password portion of the URI.

Load the bundled product data into MySQL if the table has not already been populated. This command replaces the `store_items` table with data from the bundled product CSV:

```bash
uv run python -m tdapp.data.sql_loader
```

Only run the loader when you intend to create or replace that table.

## Run the app

Run each service in a separate terminal from the repository root. Start the workflow API:

```bash
uv run uvicorn tdapp.langserve_app:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, start the Flask frontend:

```bash
uv run flask --app tdapp run --debug --host 127.0.0.1 --port 5000
```

Open <http://127.0.0.1:5000/> in a browser. Set `LANGSERVE_URL` to the workflow service's origin in the frontend environment, and list the browser-facing frontend origin(s) in the API's comma-separated `FRONTEND_ORIGINS`. The workflow API is available at <http://127.0.0.1:8000/api/workflow>; the browser uses `/api/workflow/stream`, and clients that do not need streaming can use `/api/workflow/invoke`. Requests contain `input.prompt` and `input.thread_id`; responses include both the reply and the thread ID. Chat requests require access to the configured model providers and MySQL. If the FAISS index needs to be created, the first request also requires OpenAI embedding access.

![alt text](image.png)

## Run the standalone workflow

To run the interactive terminal version instead of the web chat:

```bash
uv run python -m tdapp.core.workflow
```

This uses a sample prompt and accepts subsequent prompts in the terminal. When an interrupt requests a human-agent response, the terminal flow prompts for one; the web flow currently uses the placeholder response described above.

## Main modules

- `tdapp/langserve_app.py`: standalone LangServe workflow API
- `tdapp/pages.py`: Flask frontend page routes
- `tdapp/core/workflow_service.py`: shared workflow invocation, checkpoint restoration, interrupt resumption, and reply formatting
- `tdapp/templates/pages/home.html`: browser chat UI and local transcript persistence
- `tdapp/core/prompt_handler.py`: intent detection, structured extraction, and chat responses
- `tdapp/core/workflow.py`: LangGraph orchestration, PostgreSQL checkpointer setup, and terminal chat loop
- `tdapp/core/recipe_handler.py`: store-product lookup and structured recipe generation
- `tdapp/core/rag_handler.py`: FAISS index loading and recipe-context retrieval
- `tdapp/core/state.py`: intent, recipe, and workflow data models
- `tdapp/functions/store_products.py`: combines store products with user ingredients
- `tdapp/core/utils.py`: MySQL product query
- `tdapp/data/recipes_dataset.json`: recipe corpus used by RAG
- `tdapp/data/document_loader.py`: converts recipe JSON entries into embedding documents
- `tdapp/data/sql_loader.py`: loads the bundled CSV data into MySQL
    