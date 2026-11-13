import os

from dotenv import load_dotenv
from flask import Flask
from tdapp import pages

def create_app():
    load_dotenv()
    app=Flask(__name__)
    app.config['SECRET_KEY']='433556ae5648dc045b0854f509031ad6568790cf11130e85'
    # Keep the UI service independent while letting templates target the API service.
    app.config["LANGSERVE_URL"] = os.environ.get(
        "LANGSERVE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")
    
    app.register_blueprint(pages.bp)

    @app.context_processor
    def inject_langserve_url():
        return {"langserve_url": app.config["LANGSERVE_URL"]}

    return app
