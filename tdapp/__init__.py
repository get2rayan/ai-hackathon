from flask import Flask
from tdapp import pages

def create_app():
    app=Flask(__name__)
    app.config['SECRET_KEY']='433556ae5648dc045b0854f509031ad6568790cf11130e85'
    
    app.register_blueprint(pages.bp)
    return app
