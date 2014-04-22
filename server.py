#!/bin/env python2.7

import wikipedia as wiki
from wikipedia.exceptions import WikipediaException, DisambiguationError
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/search")
def search():
    error = None
    limit = 3

    if request.args.has_key("limit"):
        limit = request.args.get("limit")

    try:
        searchstring = request.args.get("string")
        titles = wiki.search(searchstring, results = limit);
        # Get the pages with the returned titles
        pages = map(get_page, titles)

    except WikipediaException:
        error = "Invalid search parameters"
        return render_template("search.html", error=error)

    return render_template("search.html", pages=pages)

def get_page(name):
    try:
        page = wiki.page(title=name.title())
    except DisambiguationError as e:
        # Only get the first disambiguation option
        page = wiki.page(title=e.options[0].title())
    return page

if __name__ == "__main__":
    app.run(debug=True)
