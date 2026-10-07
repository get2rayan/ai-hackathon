# AI Store Recipe Assistant

A Meijer recipe assistant prototype that extracts recipe intent, looks up store products, and generates structured recipe suggestions using retrieval-augmented generation (RAG) over a recipe dataset.

## Application flow

The standalone LangGraph workflow in `tdapp/core/workflow.py` runs these steps:

1. `PromptHandler` sends the prompt to an OpenAI chat model and extracts structured intent constrained by the `UserIntent` schema. Fields include store ID, cuisine, available ingredients, requested recipe, serving size, and store categories.
2. `RecipeHandler` passes the intent to `store_products`, which queries MySQL for products filtered by store and department. User-provided ingredients are prioritized, duplicates are removed, and the list is capped at 10 items.
3. `RecipeHandler` builds a recipe request from the intent and available products. Its OpenAI agent can call the recipe-context tool to retrieve the three most relevant recipes from a FAISS vector index.
4. The agent returns structured recipe data in `RecipeContext`, including recipe name, cuisine, ingredients, instructions, nutrition, preparation time, and source category. The workflow stores this result in `recipe_context`.

`RAGHandler` uses OpenAI `text-embedding-3-small` embeddings and the recipes in `tdapp/data/recipes_dataset.json`. If a local FAISS index is not present, it is built from the recipe JSON and saved in `faiss_index/`; otherwise the existing index is loaded. Index creation therefore requires a working OpenAI API key.

The workflow currently has no recipe-evaluation node. The Flask interface in `tdapp/pages.py` renders the prompt form, but its POST handler is not yet connected to this workflow: it calls methods/response fields that are not provided by the current `PromptHandler`. Run the LangGraph workflow independently using the command below.

## Requirements

- Python 3.13 or newer
- `uv`
- An OpenAI API key and a chat-model deployment/name accepted by the configured OpenAI endpoint
- MySQL server and a database containing the `store_items` table

## Setup

Install the project dependencies from the repository root:

```bash
uv sync
```

Create a `.env` file in the repository root with the required settings:

```dotenv
OPENAI_API_KEY=your-openai-api-key
DEPLOYMENT_NAME=your-model-or-deployment-name

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=your-database-name
```

Load the bundled product data into MySQL. The loader reads `tdapp/data/meijer_products.csv` and replaces the `store_items` table:

```bash
uv run python -m tdapp.data.sql_loader
```

Only run the loader when you intend to create or replace that table.

## Run the workflow

From the repository root:

```bash
uv run python -m tdapp.core.workflow
```

The workflow invokes the graph asynchronously using its sample prompt. A run requires OpenAI access for intent extraction, embeddings, and recipe generation, as well as MySQL access to the `store_items` table. On the first run, it also builds the local FAISS index from the recipe dataset.

## Run the Flask app

From the repository root:

```bash
uv run flask --app tdapp run --debug
```

Open <http://127.0.0.1:5000/> in a browser. The pages can be viewed, but full prompt submission is not yet integrated with the LangGraph workflow (see the application-flow note above).

## Main modules

- `tdapp/pages.py`: Flask routes and form handling
- `tdapp/core/prompt_handler.py`: OpenAI structured intent extraction
- `tdapp/core/workflow.py`: LangGraph orchestration
- `tdapp/core/recipe_handler.py`: retrieves relevant store products and generates structured recipe suggestions
- `tdapp/core/rag_handler.py`: builds/loads the FAISS index and retrieves relevant recipe context
- `tdapp/core/state.py`: intent, recipe, and LangGraph workflow data models
- `tdapp/functions/store_products.py`: combines products from the store with user ingredients
- `tdapp/core/utils.py`: MySQL product query
- `tdapp/data/recipes_dataset.json`: recipe corpus used by RAG
- `tdapp/data/document_loader.py`: converts recipe JSON entries into embedding documents
- `tdapp/data/sql_loader.py`: loads the bundled CSV data into MySQL
    