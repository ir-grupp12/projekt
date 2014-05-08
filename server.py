#!/bin/env python2.7

import re, string
import wikipedia as wiki
from wikipedia.exceptions import WikipediaException, DisambiguationError
from flask import Flask, request, render_template, json
import wikifetcher
import operator
from nltk.corpus import stopwords
from itertools import groupby
from collections import OrderedDict


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

@app.route("/wordcloud")
def wordcloud():
    wikisum = False
    context = False
    limit = 20

    # Set the search result limit using the limit parameter
    if request.args.has_key("limit"):
        limit = request.args.get("limit")

    # If wikisum is defined, use the default wikipedia summary
    if request.args.has_key("wikisum"):
        wikisum = request.args.get("wikisum") == "on"

    if request.args.has_key("context"):
        context = request.args.get("context") == "on"

    query = request.args.get("query")
    results = wikifetcher.fetch(query, limit, wikisum)

    content = "".join([content for title, content in results])

    if context:
        tags = make_context(content, query)
    else:
        tags = make_tags(content, query)
    return render_template("wordcloud.html", tags=json.dumps(tags))

def make_tags(content, query):
    query_words = query.lower().strip()
    tags = dict()
    stop = stopwords.words("english")
    for word in content.split(" "):
        w = word.lower().strip().strip(string.punctuation).strip()
        w = w.replace("'s", "")
        if w == "" or w in stop or w in query_words:
            continue
        if w not in tags:
            tags[w] = 0
        tags[w] += 1

    sorted_tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
    tags = dict()
    for i in xrange(80):
        if i >= len(sorted_tags):
            break
        tags[sorted_tags[i][0]] = sorted_tags[i][1]
    return tags

def make_context(content, query):
    # number of adjacent words on each side to extract
    NUM_ADJ_WORDS = 10
    # how much weight to give proximity
    DISTANCE_WEIGHT = 3.0
    # specifies length of data to return
    NUM_WORDS_TO_RETURN = 25

    query_word = query.lower().strip()
    content = content.lower().replace("'s", "")
    content = re.sub(' +',' ',content)
    content = "".join(l for l in content if l not in string.punctuation)
    allwords = content.split(" ")

    stop = stopwords.words("english")
    tags = dict()

    for i, word in enumerate(allwords):
        w = word.lower().strip().strip(string.punctuation).strip()
        if w == query_word:
            for x in range( 1, NUM_ADJ_WORDS+1 ):
                w = allwords[i-x] # left of query
                if w not in stop:
                    if w in tags:
                        tags[w] += 1.0/(1.0+(DISTANCE_WEIGHT*x)) # weighting
                    else:
                        tags[w] = 1.0

                w = allwords[i+x] # right of query
                if w not in stop:
                    if w in tags:
                        tags[w] += 1.0/(1.0+(DISTANCE_WEIGHT*x)) # weighting
                    else:
                        tags[w] = 1.0

    return dict(sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)[:NUM_WORDS_TO_RETURN])

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
