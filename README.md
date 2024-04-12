# TeamDragons AI app for Hackathon

This repo contains source code in python that integrates with Azure OpenAI. Note: some portions of the app use preview APIs.

## Prerequisites
- Python and related libraries should have been installed
- An existing Azure OpenAI resource and model deployment of a chat model (e.g. `gpt-35-turbo-16k`, `gpt-4`)
- To use Azure OpenAI on your data: one of the following data sources:
  - Azure AI Search Index
  - Azure CosmosDB Mongo vCore vector index
  - Elasticsearch index (preview)
  - Pinecone index (preview)
  - AzureML index (preview)

## Restore libraries
- Restore the referenced libraries by running the PIP command:
    - pip install -r requirements.txt

## Deploy the app

### Deploy from your local machine
 - The application uses python's Flask framework.  So, to deploy the application in your local, run below command from command line.
    - flask run 
    
   or to run in debug mode 
    - flask run --debug

    Open up a browser and go to http://localhost:5000 to see the code in action.
    