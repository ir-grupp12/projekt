#!/bin/env python2.7

import re, string
import wikipedia as wiki
from wikipedia.exceptions import WikipediaException, DisambiguationError
from flask import Flask, request, render_template, json, jsonify
import wikifetcher
import operator
from nltk.corpus import stopwords
from itertools import groupby
from collections import OrderedDict


app = Flask(__name__)

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/wordcloud")
def wordcloud():
    wikisum = False
    context = False
    limit = 3
    dist = 10
    numwords = 20

    # Set the search result limit using the limit parameter
    if request.args.has_key("limit"):
        limit = request.args.get("limit")

    if request.args.has_key("context"):
        context = request.args.get("context") == "on"
        
    if request.args.has_key("dist"):
        dist = max(1,min(200, int(request.args.get("dist"))))

    if request.args.has_key("numwords"):
        numwords = max(1,min(200, int(request.args.get("numwords"))))


    query = request.args.get("query")

    if query.strip() == "":
        return hello()
    
    results = wikifetcher.fetch(query, limit)

    docs = [doc for title, doc in results]

    if context:
        tags = make_context(docs, query, normalised=request.args.has_key("norm"), NUM_ADJ_WORDS=dist, NUM_WORDS_TO_RETURN=numwords)
    else:
        tags = make_tags(docs, query, normalised=request.args.has_key("norm"), NUM_WORDS_TO_RETURN=numwords)

    if request.args.has_key("debug"):
        for tag in tags:
            print "'"+tag+"' has score " + str(tags[tag])

    return render_template("wordcloud.html", tags=json.dumps(tags), debug=request.args.has_key("debug"))

# params:
#        docs: an array of documents
#        query: the search string
# returns:
#        tags: a dict of tags and rankings
def make_tags(docs, query, normalised=False, NUM_WORDS_TO_RETURN = 80):   
    query_words = query.lower().strip()
    tags = dict()
    stop = stopwords.words("english")
    for doc in docs:
        words = wordify(doc)
        doclength = float(len(words))
        for word in words:
            w = word.lower().strip().strip(string.punctuation).strip()
            w = w.replace("'s", "")
            if w == "" or w in stop or w in query_words:
                continue
            if w not in tags:
                tags[w] = 0
            tags[w] += 1/(doclength if normalised else 1)

    sorted_tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
    
    tags = dict()
    for i in xrange(len(sorted_tags)):
        if i >= NUM_WORDS_TO_RETURN:
            break
        tags[sorted_tags[i][0]] = sorted_tags[i][1]
 
    return tags
    


def make_context(docs, query, normalised=False, NUM_ADJ_WORDS = 10, NUM_WORDS_TO_RETURN = 80):
    # how much weight to give proximity
    DISTANCE_WEIGHT = 3.0
    query_word = query.lower().strip()

    stop = stopwords.words("english")
    tags = dict()
    
    def _update_distance(words):
        distance = 0
        for w in words: 
            distance += 1           
            if w in stop or w in query_word:
                continue
                
            if w not in tags: #initialize (because of lookahead)
                tags[w] = 1.0/(doclength if normalised else 1)
                
            tags[w] += (1.0/(DISTANCE_WEIGHT*distance) + (1.0/doclength if normalised else 0)) # weighting
            
    for doc in docs:
        words = wordify(doc)
        doclength = float(len(words))

        for i, word in enumerate(words):
            w = word.lower().strip().strip(string.punctuation).strip('\n\r\t ')
            
            if w == "" or w in stop:
                continue
                
            if w not in tags and w not in query_word: #initialize
                tags[w] = 1.0/(doclength if normalised else 1)           
            
            if w in query_word:
                # update words nearby
                left_of = words[max(0, i - NUM_ADJ_WORDS): i]
                right_of = words[i: min(i - NUM_ADJ_WORDS, len(words))]
                
                _update_distance(left_of)
                _update_distance(right_of)

    return dict(sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)[:NUM_WORDS_TO_RETURN])

#
# Takes a document and returns an array of the words
#
def wordify(doc):
        doc = doc.lower().replace("'s", "")
        doc = re.sub('[\n\r\t ]+',' ',doc)
        doc = "".join(l for l in doc if l not in string.punctuation)
        return doc.split(" ")

#
# Takes a WikipediaPage object as parameter and returns
# a tuple of (title, summary)
#
def summarize(page):
    title = page[0]
    summary = re.split(r'\. ', page[1])[0] + ".";
    return (title, summary)

def termfreq(doc, term):
    count = 0
    for word in doc:
        if word == term:
            count = count + 1
    return count

if __name__ == "__main__":
    app.run(debug=True)
