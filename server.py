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
    adj_words = 10
    query_word = query.lower().strip()
    allwords = []
    content = content.lower()
    for word in stopwords.words("english"): # this is likely ridiculously inefficient
        content = string.replace(content, " "+word+" ", " ") # super ugly

    #content = re.sub(' +',' ',content) # remove double spaces
    content = "".join(l for l in content if l not in string.punctuation) # remove punctuation
    indices = [m.start() for m in re.finditer(query_word, content)] # list of indices where query_word occurs

    for i in indices:
        #print content[i-30 : i+30+len(query_word)] # prints the 30 characters on each side of the word for debug purposes
        leftwords  = content[:i].split(" ")[-1-adj_words : -1] # makes list of adjacent words to the left of query_word
        rightwords = content[i:].split(" ")[1 : 1+adj_words] # makes list of adjacent words to the right of query_word
        allwords += leftwords+rightwords # add to list of all adjacent words

    allwords.sort()
    occurences = [len(list(group)) for key, group in groupby(allwords)] # makes list of number of occurences, eg [1,1,3,1,2,4]

    uniquewords = [ key for key,_ in groupby(allwords)] # removes duplicates from a sorted list
    context_dict = dict(zip(uniquewords, occurences)) # combines occurence list and list of words (without duplicates) into dict

    tempdict = OrderedDict(sorted(context_dict.items(), key=lambda t: t[1])) # sorts dict based on key value
    sorteddict = tempdict.items()
    sorteddict.reverse() # reverse sorting order of dict (more occurences = first)
    OrderedDict(sorteddict)

    return dict(sorteddict[:50]) # how many words to return

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
