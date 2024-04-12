from flask import Blueprint, flash, render_template, request
from .core import prompt

bp=Blueprint("pages", __name__)


@bp.route("/", methods=('GET', 'POST'))
def home():    

    if request.method=='POST':
        userprompt = request.form['userPrompt'].strip()
        if not userprompt:            
            flash('Please enter a valid user prompt')
            return render_template("pages/home.html")
        else:           
            p = prompt.Prompt() 
            extract_resp = p.extractUserPrompt(userprompt)            
            recipe_resp = p.get_custom_recipes(extract_resp)

            if extract_resp.tool_calls is not None:
                prompt_msg = extract_resp.tool_calls[0].function.arguments
            else:
                prompt_msg = extract_resp.content
            
            # messages = {
            #     "content":{
            #         'extract_args': extract_resp.tool_calls[0].function.arguments,
            #         'recipe_resp':recipe_resp
            #     }
            # }
            return render_template("pages/home.html", extract_args= prompt_msg , recipe_resp=recipe_resp)
    
    return render_template("pages/home.html")


@bp.route("/about")
def about():
    return render_template("pages/about.html")