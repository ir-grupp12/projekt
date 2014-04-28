#!/bin/env python2.7

import re
import wikipedia as wiki
from wikipedia.exceptions import WikipediaException, DisambiguationError
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/<searchstring>")
def search(searchstring):
    error = None
    wikisum = False
    limit = 3

    # Set the search result limit using the limit parameter
    if request.args.has_key("limit"):
        limit = request.args.get("limit")

    # If wikisum is defined, use the default wikipedia summary
    if request.args.has_key("wikisum"):
        wikisum = True

    try:
        searchstring = searchstring.replace("_", "%20") #request.args.get("string")
        print searchstring
        titles = wiki.search(searchstring, results = limit);
        # Get the pages with the returned titles
        pages = map(get_page, titles)

    except WikipediaException:
        error = "Invalid search parameters"
        return render_template("search.html", error=error)

    results = []
    if not wikisum:
        results = map(summarize, pages)
    else:
        results = [(x.title, x.summary) for x in pages]

    return render_template("search.html", results=results)

#
# Takes a wikipedia article title and gets
# the WikipediaPage object for that page.
#
def get_page(name):
    try:
        page = wiki.page(title=name.title())
    except DisambiguationError as e:
        # Only get the first disambiguation option for now
        page = wiki.page(title=e.options[0].title())
    return page

#
# Takes a WikipediaPage object as parameter and returns
# a tuple of (title, summary)
#
def summarize(page):
    title = page.title
    summary = re.split(r'\. ', page.content)[0] + ".";
    return (title, summary)

if __name__ == "__main__":
    app.run(debug=True)
