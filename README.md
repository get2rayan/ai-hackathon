# AI Store Recipe Assistant

A Flask-based Meijer recipe assistant prototype. It extracts recipe intent from a natural-language prompt, finds relevant products for a store, and uses those products as recipe inputs.

## Application flow

The standalone LangGraph workflow currently implements this path:

1. `PromptHandler` sends the user's prompt to an OpenAI chat model and validates the response against the `UserIntent` JSON schema. The extracted fields include store ID, cuisine, available ingredients, recipe name, serving size, and store categories.
2. `RecipeHandler` receives the structured intent and asks `store_products` for relevant products.
3. `store_products` queries MySQL through `Utilities`, filtered by store and department. User-provided ingredients are placed first, duplicates are removed, and the result is limited to 10 items.
4. The workflow returns the extracted intent and product list in its state.

The workflow is defined in `tdapp/core/workflow.py`. Its current graph ends after fetching recipe items; it does not yet generate a recipe or evaluate one.

The Flask interface is defined in `tdapp/pages.py` and renders the home form and its result fields. **The form's POST handler is not currently wired to the workflow:** it calls `PromptHandler.get_custom_recipes`, which is not implemented on `PromptHandler`. The workflow can be run independently using the command below; the web form's full submit flow needs that integration completed.

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

The workflow prints the Mermaid graph source and then invokes it with its sample prompt. The graph calls OpenAI and MySQL, so valid credentials, database access, and product data are needed for a complete run.

## Run the Flask app

From the repository root:

```bash
uv run flask --app tdapp run --debug
```

Open <http://127.0.0.1:5000/> in a browser. The home page and About page can be viewed; submitting a prompt requires wiring the Flask handler to the workflow as noted above.

## Main modules

- `tdapp/pages.py`: Flask routes and form handling
- `tdapp/core/prompt_handler.py`: OpenAI structured intent extraction
- `tdapp/core/workflow.py`: LangGraph orchestration
- `tdapp/core/recipe_handler.py`: maps intent to relevant products
- `tdapp/functions/store_products.py`: combines products from the store with user ingredients
- `tdapp/core/utilities.py`: MySQL product query
- `tdapp/data/sql_loader.py`: loads the bundled CSV data into MySQL
    