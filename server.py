#!/bin/env python2.7

import re
import wikipedia as wiki
from wikipedia.exceptions import WikipediaException, DisambiguationError
from flask import Flask, request, render_template
import wikifetcher

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/search")
def search():
    error = None
    wikisum = False
    limit = 20

    # Set the search result limit using the limit parameter
    if request.args.has_key("limit"):
        limit = request.args.get("limit")

    # If wikisum is defined, use the default wikipedia summary
    if request.args.has_key("wikisum"):
        wikisum = request.args.get("wikisum") == "on"

    try:
        query = request.args.get("query")
        results = wikifetcher.fetch(query, limit, wikisum)

    except WikipediaException as ex:
        print ex
        error = "Invalid search parameters"
        return render_template("search.html", error=error)

    if not wikisum:
        results = map(summarize, results)   

    return render_template("search.html", results=results)

#
# Takes a WikipediaPage object as parameter and returns
# a tuple of (title, summary)
#
def summarize(page):
    title = page[0]
    summary = re.split(r'\. ', page[1])[0] + ".";
    return (title, summary)

if __name__ == "__main__":
    app.run(debug=True)
