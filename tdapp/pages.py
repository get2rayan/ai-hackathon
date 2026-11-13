from flask import Blueprint, render_template

bp=Blueprint("pages", __name__)


@bp.get("/")
def home():
    """Render the standalone frontend."""
    return render_template("pages/home.html")


@bp.route("/about")
def about():
    """Render the about page."""
    return render_template("pages/about.html")